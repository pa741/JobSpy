from __future__ import annotations

import math
import time
from datetime import datetime, timedelta, timezone

from jobspy.freehire.constant import (
    agent_search_endpoint,
    base_url,
    cities_endpoint,
    default_user_agent,
    description_format_map,
    employment_type_map,
    geography_facets,
    headers,
    job_type_map,
    max_offset,
    max_page_size,
    salary_period_map,
    search_endpoint,
    site_url,
)
from jobspy.model import (
    Compensation,
    Country,
    JobPost,
    JobResponse,
    Location,
    Scraper,
    ScraperInput,
    Site,
)
from jobspy.util import create_logger, create_session

log = create_logger("FreeHire")


class FreeHire(Scraper):
    """
    Reads freehire.me's public HTTP API.

    Unlike every other source here this is not a scrape: freehire is itself an
    aggregator with a documented, unauthenticated JSON API, so the adapter is
    field mapping rather than HTML parsing. It covers IT/tech roles only.
    """

    def __init__(
        self,
        proxies: list[str] | str | None = None,
        ca_cert: str | None = None,
        user_agent: str | None = None,
    ):
        super().__init__(
            Site.FREEHIRE, proxies=proxies, ca_cert=ca_cert, user_agent=user_agent
        )
        self.scraper_input = None
        self.session = None
        self.headers = None
        self.searched_city = None
        self.searched_country = None

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        self.scraper_input = scraper_input
        # Deliberately unproxied. There are no bot defenses to route around, and
        # the full-description pull is the largest payload of a run - sending it
        # through metered residential IPs spends money for nothing. Proxies still
        # apply to every scraped board.
        self.session = create_session(
            proxies=None, ca_cert=self.ca_cert, is_tls=False, has_retry=True
        )
        self.headers = dict(headers)
        self.headers["User-Agent"] = self.user_agent or default_user_agent
        if scraper_input.freehire_api_key:
            # Search needs no key; one only identifies the caller.
            self.headers["Authorization"] = f"Bearer {scraper_input.freehire_api_key}"

        endpoint = (
            agent_search_endpoint
            if scraper_input.freehire_full_description
            else search_endpoint
        )
        params = self._build_params()
        cutoff = self._posted_cutoff()

        job_list: list[JobPost] = []
        seen_slugs: set[str] = set()
        results_wanted = scraper_input.results_wanted or 10
        start_offset = scraper_input.offset or 0
        offset = start_offset

        while len(job_list) < results_wanted:
            limit = min(max_page_size, results_wanted - len(job_list))
            if offset + limit > max_offset:
                log.warning(
                    f"stopping at offset {offset}: freehire refuses offset + limit "
                    f"beyond {max_offset}, so the remaining "
                    f"{results_wanted - len(job_list)} result(s) are unreachable by paging"
                )
                break

            payload = self._get(endpoint, {**params, "limit": limit, "offset": offset})
            if payload is None:
                break

            meta = payload.get("meta") or {}
            if offset == start_offset:
                self._report_ignored_params(meta)
                log.info(f"{meta.get('total', 'unknown')} posting(s) match this search")

            hits = payload.get("data") or []
            if not hits:
                break

            for hit in hits:
                slug = hit.get("public_slug")
                if not slug or slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                job_post = self._to_job_post(hit)
                if job_post is None:
                    continue
                if cutoff and (
                    job_post.date_posted is None or job_post.date_posted < cutoff
                ):
                    continue
                job_list.append(job_post)
                if len(job_list) >= results_wanted:
                    break

            offset += len(hits)
            total = meta.get("total")
            if len(hits) < limit or (isinstance(total, int) and offset >= total):
                break

        return JobResponse(jobs=job_list)

    def _get(self, endpoint: str, params: dict) -> dict | None:
        """
        One GET, paced against the advertised budget. Returns None when the page
        could not be read, which ends paging rather than losing the run.
        """
        try:
            response = self.session.get(
                f"{base_url}{endpoint}",
                params=params,
                headers=self.headers,
                timeout=self.scraper_input.request_timeout,
            )
        except Exception as e:
            log.error(f"request failed: {e}")
            return None

        if response.status_code == 429:
            wait = self._int_header(response, "Retry-After") or 5
            log.warning(f"rate limited, waiting {wait}s")
            time.sleep(wait)
            return self._get(endpoint, params)

        if not response.ok:
            log.error(f"HTTP {response.status_code}: {response.text[:200]}")
            return None

        # Absent headers mean the limiter could not run, not that there is no
        # limit, so only an actual low reading is acted on.
        remaining = self._int_header(response, "X-RateLimit-Remaining")
        if remaining is not None and remaining < 5:
            reset = self._int_header(response, "X-RateLimit-Reset") or 1
            log.info(f"{remaining} request(s) left in budget, pausing {reset}s")
            time.sleep(reset)

        try:
            return response.json()
        except Exception as e:
            log.error(f"could not decode response: {e}")
            return None

    @staticmethod
    def _int_header(response, name: str) -> int | None:
        try:
            return int(response.headers[name])
        except (KeyError, TypeError, ValueError):
            return None

    def _build_params(self) -> dict:
        params: dict = {}
        scraper_input = self.scraper_input

        if scraper_input.search_term:
            params["q"] = scraper_input.search_term

        params.update(self._resolve_geography())

        if scraper_input.is_remote:
            params["work_mode"] = "remote"

        if scraper_input.job_type:
            employment_type = job_type_map.get(scraper_input.job_type)
            if employment_type:
                params["employment_type"] = employment_type
            else:
                log.warning(
                    f"freehire has no employment type for "
                    f"{scraper_input.job_type.name.lower()}; ignoring the filter"
                )

        if scraper_input.hours_old:
            # The API's freshness filter is whole days. The exact hours_old cut
            # is applied to posted_at afterwards; this only narrows the fetch.
            params["posted_within_days"] = max(
                1, math.ceil(scraper_input.hours_old / 24)
            )

        if scraper_input.freehire_full_description:
            fmt = description_format_map.get(
                scraper_input.description_format.value
                if scraper_input.description_format
                else "markdown"
            )
            if fmt:
                params["description_format"] = fmt

        # Last, so an explicit filter always wins over anything derived above.
        if scraper_input.freehire_filters:
            params.update(scraper_input.freehire_filters)

        return params

    def _resolve_geography(self) -> dict:
        """
        Picks exactly one geography level.

        regions, countries and cities are ONE OR-group, not three filters that
        intersect: countries=gb&cities=London means "the UK or London", which is
        wider than countries=gb alone. So naming two levels to be specific does
        the opposite, and this returns at most one key.
        """
        scraper_input = self.scraper_input

        explicit = scraper_input.freehire_filters or {}
        if any(facet in explicit for facet in geography_facets):
            # The caller has chosen a level; adding another would widen it.
            return {}

        country_code = self.searched_country = self._country_code()
        location = (scraper_input.location or "").strip()

        if location:
            city = self._resolve_city(location.split(",")[0].strip(), country_code)
            if city:
                self.searched_city = city
                return {"cities": city}
            log.warning(
                f"freehire has no canonical city matching {location!r}; "
                + (
                    f"falling back to the whole of {country_code}"
                    if country_code
                    else "searching without a geography filter"
                )
            )

        return {"countries": country_code} if country_code else {}

    def _country_code(self) -> str | None:
        """ISO 3166-1 alpha-2 for the search country, or None when it has no single one."""
        country = self.scraper_input.country
        if not country or country in (Country.WORLDWIDE, Country.US_CANADA):
            return None
        return country.indeed_domain_value[1].lower()

    def _resolve_city(self, city: str, country_code: str | None) -> str | None:
        """
        The cities facet holds canonical display names and matches nothing on a
        near miss, so a raw location string has to be resolved before it is used.
        City names are not unique ("London" is both gb and ca), hence the country
        qualifier.
        """
        if not city:
            return None
        params = {"q": city}
        if country_code:
            params["country"] = country_code
        payload = self._get(cities_endpoint, params)
        if not payload:
            return None
        for match in payload.get("data") or []:
            value = match.get("value")
            if value and value.casefold() == city.casefold():
                return value
        return None

    def _posted_cutoff(self):
        """The exact hours_old boundary, as a date. None when unfiltered."""
        if not self.scraper_input.hours_old:
            return None
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=self.scraper_input.hours_old
        )
        return cutoff.date()

    @staticmethod
    def _report_ignored_params(meta: dict) -> None:
        """
        freehire drops an unreadable parameter instead of refusing the request,
        so a typo silently returns the entire catalogue and looks exactly like a
        filter that legitimately matched everything. The key is absent on a clean
        request, so its presence alone is the signal.
        """
        for ignored in meta.get("ignored_params") or []:
            suggestion = ignored.get("did_you_mean")
            log.warning(
                f"freehire ignored the parameter {ignored.get('param')!r}"
                + (f"; did you mean {suggestion!r}?" if suggestion else "")
                + " - the result is NOT filtered by it"
            )

    def _to_job_post(self, hit: dict) -> JobPost | None:
        slug = hit.get("public_slug")
        title = hit.get("title")
        if not slug or not title:
            return None

        enrichment = hit.get("enrichment") or {}
        work_mode = hit.get("work_mode")
        company_slug = hit.get("company_slug")

        return JobPost(
            id=f"fh-{slug}",
            title=title,
            company_name=hit.get("company"),
            # The freehire listing page, matching how job_url points at the board
            # elsewhere; the employer's own application link is job_url_direct.
            job_url=f"{site_url}/jobs/{slug}",
            job_url_direct=hit.get("url"),
            location=self._location(hit),
            description=hit.get("description"),
            job_type=self._job_type(enrichment),
            compensation=self._compensation(enrichment),
            date_posted=self._date_posted(hit.get("posted_at")),
            # None, not False, when freehire could not resolve the work mode -
            # "not stated" is not the same as "not remote".
            is_remote=work_mode == "remote" if work_mode else None,
            company_url=f"{site_url}/companies/{company_slug}" if company_slug else None,
            skills=hit.get("skills"),
            source_board=hit.get("source"),
        )

    def _location(self, hit: dict) -> Location:
        """
        Built from the resolved facets, not the posting's own `location` string,
        which freehire serves verbatim and unnormalized.

        `cities` and `countries` are two flat arrays with nothing linking them,
        so on a posting open in several places the first of each is not a pair.
        One role really is tagged [Amsterdam, Belgrade, ..., London] across nine
        countries; reading position 0 off both would file it under "Amsterdam,
        GB", a place it is not open in.

        So a city and a country are named together only when the pairing is
        certain: either the city is the one resolved inside the searched
        country, or the posting names exactly one of each. Otherwise whichever
        side is unambiguous is named alone.
        """
        cities = hit.get("cities") or []
        countries = hit.get("countries") or []
        country = self.searched_country

        # Matched case-insensitively - freehire stores the odd city lowercase -
        # but reported in the canonical form the facet was queried with, so the
        # column groups cleanly.
        matched_city = (
            self.searched_city
            if any(
                self.searched_city and c.casefold() == self.searched_city.casefold()
                for c in cities
            )
            else None
        )

        if matched_city and country in countries:
            return Location(city=matched_city, country=country.upper())

        if len(cities) == 1 and len(countries) == 1:
            return Location(city=cities[0], country=countries[0].upper())

        city = matched_city or (cities[0] if len(cities) == 1 else None)
        if country not in countries:
            country = countries[0] if len(countries) == 1 else None
        return Location(city=city, country=country.upper() if country else None)

    @staticmethod
    def _job_type(enrichment: dict) -> list | None:
        job_type = employment_type_map.get(enrichment.get("employment_type"))
        return [job_type] if job_type else None

    @staticmethod
    def _compensation(enrichment: dict) -> Compensation | None:
        min_amount = enrichment.get("salary_min")
        max_amount = enrichment.get("salary_max")
        if min_amount is None and max_amount is None:
            return None
        return Compensation(
            interval=salary_period_map.get(enrichment.get("salary_period")),
            min_amount=min_amount,
            max_amount=max_amount,
            currency=enrichment.get("salary_currency"),
        )

    @staticmethod
    def _date_posted(posted_at: str | None):
        if not posted_at:
            return None
        try:
            return datetime.fromisoformat(posted_at.replace("Z", "+00:00")).date()
        except ValueError:
            log.warning(f"could not parse posted_at {posted_at!r}")
            return None
