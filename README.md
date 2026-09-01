<img src="https://github.com/cullenwatson/JobSpy/assets/78247585/ae185b7e-e444-4712-8bb9-fa97f53e896b" width="400">

> **This is a fork.** Upstream [speedyapply/JobSpy](https://github.com/speedyapply/JobSpy)
> has not merged since 2026-02-18. This fork adds LinkedIn applicant counts, whether a
> LinkedIn application is completed offsite, and a
> [freehire.me](https://freehire.me) source, and is consumed by
> [pa741/job-scrapper](https://github.com/pa741/job-scrapper) pinned to a tag. Work lands on
> the `patches` branch; `main` tracks upstream so `patches` stays rebaseable.

**JobSpy** is a job scraping library with the goal of aggregating all the jobs from popular job boards with one tool.

## Features

- Scrapes job postings from **LinkedIn**, **Indeed**, **Glassdoor**, **Google**, **ZipRecruiter**, & other job boards concurrently
- Reads **freehire.me**'s public API, which aggregates 227 further ATS/boards (IT/tech roles only)
- Aggregates the job postings in a dataframe
- Proxies support to bypass blocking

![jobspy](https://github.com/cullenwatson/JobSpy/assets/78247585/ec7ef355-05f6-4fd3-8161-a817e31c5c57)

### Installation

```
pip install -U python-jobspy
```

_Python version >= [3.10](https://www.python.org/downloads/release/python-3100/) required_

### Usage

```python
import csv
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "zip_recruiter", "google"], # "glassdoor", "bayt", "naukri", "bdjobs", "freehire"
    search_term="software engineer",
    google_search_term="software engineer jobs near San Francisco, CA since yesterday",
    location="San Francisco, CA",
    results_wanted=20,
    hours_old=72,
    country_indeed='USA',
    
    # linkedin_fetch_description=True # gets more info such as description, direct job url (slower)
    # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
)
print(f"Found {len(jobs)} jobs")
print(jobs.head())
jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False) # to_excel
```

### Output

```
SITE           TITLE                             COMPANY           CITY          STATE  JOB_TYPE  INTERVAL  MIN_AMOUNT  MAX_AMOUNT  JOB_URL                                            DESCRIPTION
indeed         Software Engineer                 AMERICAN SYSTEMS  Arlington     VA     None      yearly    200000      150000      https://www.indeed.com/viewjob?jk=5e409e577046...  THIS POSITION COMES WITH A 10K SIGNING BONUS!...
indeed         Senior Software Engineer          TherapyNotes.com  Philadelphia  PA     fulltime  yearly    135000      110000      https://www.indeed.com/viewjob?jk=da39574a40cb...  About Us TherapyNotes is the national leader i...
linkedin       Software Engineer - Early Career  Lockheed Martin   Sunnyvale     CA     fulltime  yearly    None        None        https://www.linkedin.com/jobs/view/3693012711      Description:By bringing together people that u...
linkedin       Full-Stack Software Engineer      Rain              New York      NY     fulltime  yearly    None        None        https://www.linkedin.com/jobs/view/3696158877      Rain’s mission is to create the fastest and ea...
zip_recruiter Software Engineer - New Grad       ZipRecruiter      Santa Monica  CA     fulltime  yearly    130000      150000      https://www.ziprecruiter.com/jobs/ziprecruiter...  We offer a hybrid work environment. Most US-ba...
zip_recruiter Software Developer                 TEKsystems        Phoenix       AZ     fulltime  hourly    65          75          https://www.ziprecruiter.com/jobs/teksystems-0...  Top Skills' Details• 6 years of Java developme...

```

### Parameters for `scrape_jobs()`

```plaintext
Optional
├── site_name (list|str): 
|    linkedin, zip_recruiter, indeed, glassdoor, google, bayt, bdjobs, freehire
|    (default is all)
│
├── search_term (str)
|
├── google_search_term (str)
|     search term for google jobs. This is the only param for filtering google jobs.
│
├── location (str)
│
├── distance (int): 
|    in miles, default 50
│
├── job_type (str): 
|    fulltime, parttime, internship, contract
│
├── proxies (list): 
|    in format ['user:pass@host:port', 'localhost']
|    each job board scraper will round robin through the proxies
|
├── is_remote (bool)
│
├── results_wanted (int): 
|    number of job results to retrieve for each site specified in 'site_name'
│
├── easy_apply (bool): 
|    filters for jobs that are hosted on the job board site (LinkedIn easy apply filter no longer works)
|
├── user_agent (str): 
|    override the default user agent which may be outdated
│
├── description_format (str): 
|    markdown, html (Format type of the job descriptions. Default is markdown.)
│
├── offset (int): 
|    starts the search from an offset (e.g. 25 will start the search from the 25th result)
│
├── hours_old (int): 
|    filters jobs by the number of hours since the job was posted 
|    (ZipRecruiter and Glassdoor round up to next day.)
│
├── verbose (int) {0, 1, 2}: 
|    Controls the verbosity of the runtime printouts 
|    (0 prints only errors, 1 is errors+warnings, 2 is all logs. Default is 2.)

├── linkedin_fetch_description (bool): 
|    fetches full description, direct job url and applicant count for LinkedIn (Increases requests by O(n))
│
├── linkedin_company_ids (list[int]): 
|    searches for linkedin jobs with specific company ids
|
├── freehire_full_description (bool):
|    fetches each posting's full description instead of the search index's
|    truncated preview. Default is True; costs nothing extra per posting,
|    just a larger response.
|
├── freehire_api_key (str):
|    a freehire personal API key, sent as a bearer token. Optional - search
|    is unauthenticated, and a key only identifies the caller.
|
├── freehire_filters (dict):
|    any additional freehire facet, passed through verbatim and applied over
|    the filters derived from the parameters above, e.g.
|    {"skills": "go", "seniority": "senior", "employment_type": "contract"}.
|    Call https://freehire.me/api/v1/jobs/facets for the live vocabulary.
|
├── country_indeed (str): 
|    filters the country on Indeed & Glassdoor (see below for correct spelling)
|
├── enforce_annual_salary (bool): 
|    converts wages to annual salary
|
├── ca_cert (str)
|    path to CA Certificate file for proxies
```

```
├── Indeed limitations:
|    Only one from this list can be used in a search:
|    - hours_old
|    - job_type & is_remote
|    - easy_apply
│
└── LinkedIn limitations:
|    Only one from this list can be used in a search:
|    - hours_old
|    - easy_apply
```

## Supported Countries for Job Searching

### **LinkedIn**

LinkedIn searches globally & uses only the `location` parameter. 

### **ZipRecruiter**

ZipRecruiter searches for jobs in **US/Canada** & uses only the `location` parameter.

### **Indeed / Glassdoor**

Indeed & Glassdoor supports most countries, but the `country_indeed` parameter is required. Additionally, use the `location`
parameter to narrow down the location, e.g. city & state if necessary. 

You can specify the following countries when searching on Indeed (use the exact name, * indicates support for Glassdoor):

|                      |              |            |                |
|----------------------|--------------|------------|----------------|
| Argentina            | Australia*   | Austria*   | Bahrain        |
| Belgium*             | Brazil*      | Canada*    | Chile          |
| China                | Colombia     | Costa Rica | Czech Republic |
| Denmark              | Ecuador      | Egypt      | Finland        |
| France*              | Germany*     | Greece     | Hong Kong*     |
| Hungary              | India*       | Indonesia  | Ireland*       |
| Israel               | Italy*       | Japan      | Kuwait         |
| Luxembourg           | Malaysia     | Mexico*    | Morocco        |
| Netherlands*         | New Zealand* | Nigeria    | Norway         |
| Oman                 | Pakistan     | Panama     | Peru           |
| Philippines          | Poland       | Portugal   | Qatar          |
| Romania              | Saudi Arabia | Singapore* | South Africa   |
| South Korea          | Spain*       | Sweden     | Switzerland*   |
| Taiwan               | Thailand     | Turkey     | Ukraine        |
| United Arab Emirates | UK*          | USA*       | Uruguay        |
| Venezuela            | Vietnam*     |            |                |

### **Bayt**

Bayt only uses the search_term parameter currently and searches internationally

### **freehire**

freehire is an API, not a scrape: no proxy is used for it even when `proxies` is set, since
there is nothing to route around and it is the largest payload of a run.

`location` and `country_indeed` are resolved to freehire's own geography facets. Note that
its `regions`, `countries` and `cities` facets are a single OR-group rather than three
filters that intersect, so `countries=gb&cities=London` means "the UK **or** London" - wider
than either alone. The adapter therefore picks exactly one level: the canonical city when
`location` resolves to one, otherwise the country. Pass `freehire_filters={"regions": ...}`
to choose the level yourself.

Coverage is IT/tech roles only, so it complements the general-purpose boards rather than
replacing one.

It also carries signals no scraped board offers: `freshness_class`, `posting_age_days`,
`repost_count` and `fake_freshness` say how much of a posting's own freshness claim to
believe. A scraped board tells you what a listing says about itself; these say whether the
role has been recycled or the date refreshed. All four are populated on every posting.



## The apply URL, and why `offsite_apply` exists

LinkedIn used to publish the employer's own apply URL on the signed-out job page, inside
`<code id="applyUrl">`, and `_parse_job_url_direct` read it into `job_url_direct`. **It stopped,
and the failure was silent** - the selector simply matched nothing and every posting came back
with no direct link, which is indistinguishable from Easy Apply.

Measured on 2026-09-01 against a live corpus of 4,470 LinkedIn postings: **every one** had no
direct link, while the detail page had been fetched for 98.4% of them - so the scraper looked and
there was nothing to find. Checked against the live pages directly: `<code id="applyUrl">` is
gone, `/job-apply/{id}` and every other apply-redirect endpoint answers 404, there is no JSON-LD,
and a guest job page now contains **no non-LinkedIn URL anywhere on it**. The URL is not
obtainable without authenticating.

What LinkedIn does still publish is whether the application is offsite, in two independent
places: the apply button's `apply-button__offsite-apply-icon-svg` icon, and the sign-in modal's
`public_jobs_apply-link-offsite_*` impression id. `_parse_offsite_apply` reads both, plus the
tracking-control name, plus `job_url_direct` where it is still available.

**It returns `None`, not `False`, when nothing is recognisable.** A page that did not render its
apply affordance - a signup wall, a truncated response, the next redesign - establishes nothing,
and reporting that as "LinkedIn hosts this application" is the fault this replaced. Verified
against live LinkedIn: 6/6 unfiltered postings return `True`, and 6/6 under LinkedIn's own
`f_AL=true` Easy Apply filter return `False`.

`job_url_direct` is unchanged and still read first - a URL is strictly better than a flag, other
locales may still serve it, and a restoration would flow straight back through it.

Run the tests with `pytest tests/`. The fixtures are synthetic markup reduced to the attributes
the parser reads; no scraped job content is committed.

## Notes
* Indeed is the best scraper currently with no rate limiting.  
* All the job board endpoints are capped at around 1000 jobs on a given search.  
* LinkedIn is the most restrictive and usually rate limits around the 10th page with one ip. Proxies are a must basically.
* freehire is the exception to both: it publishes 600 req/min and reports your remaining budget on every response, and paging is capped at offset 10000 rather than ~1000 jobs.

## Frequently Asked Questions

---
**Q: Why is Indeed giving unrelated roles?**  
**A:** Indeed searches the description too.

- use - to remove words
- "" for exact match

Example of a good Indeed query

```py
search_term='"engineering intern" software summer (java OR python OR c++) 2025 -tax -marketing'
```

This searches the description/title and must include software, summer, 2025, one of the languages, engineering intern exactly, no tax, no marketing.

---

**Q: No results when using "google"?**  
**A:** You have to use super specific syntax. Search for google jobs on your browser and then whatever pops up in the google jobs search box after applying some filters is what you need to copy & paste into the google_search_term. 

---

**Q: Received a response code 429?**  
**A:** This indicates that you have been blocked by the job board site for sending too many requests. All of the job board sites are aggressive with blocking. We recommend:

- Wait some time between scrapes (site-dependent).
- Try using the proxies param to change your IP address.

---

### JobPost Schema

```plaintext
JobPost
├── title
├── company
├── company_url
├── job_url
├── location
│   ├── country
│   ├── city
│   ├── state
├── is_remote
├── description
├── job_type: fulltime, parttime, internship, contract
├── job_function
│   ├── interval: yearly, monthly, weekly, daily, hourly
│   ├── min_amount
│   ├── max_amount
│   ├── currency
│   └── salary_source: direct_data, description (parsed from posting)
├── date_posted
└── emails

Linkedin specific
├── job_level
├── applicants          (verbatim caption, e.g. "Over 200 applicants")
├── applicant_count     (the figure parsed out of it, e.g. 200)
└── offsite_apply       (True = applies on the employer's own system, False = Easy Apply,
                         None = not established. See "The apply URL" below.)

Linkedin & Indeed specific
└── company_industry

Indeed specific
├── company_country
├── company_addresses
├── company_employees_label
├── company_revenue_label
├── company_description
└── company_logo

freehire specific
├── source_board        (which of freehire's crawled boards the posting came from)
├── summary             (1-2 sentence synopsis)
├── freshness_class     (fresh | stale | likely-evergreen)
├── posting_age_days
├── repost_count        (times this role has been reposted)
└── fake_freshness      (stated posting date looks refreshed rather than real)

freehire also fills job_level, experience_range and company_num_employees,
which are not freehire-only concepts and so reuse the existing columns.

Naukri specific
├── skills
├── experience_range
├── company_rating
├── company_reviews_count
├── vacancy_count
└── work_from_home_type
```
