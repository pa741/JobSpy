from jobspy.model import CompensationInterval, JobType

base_url = "https://freehire.me/api/v1"

search_endpoint = "/jobs/search"
# Same query surface as /jobs/search, but every hit carries the full description
# read from the database instead of the search index's truncated preview.
agent_search_endpoint = "/agent/jobs/search"
cities_endpoint = "/geo/cities"

site_url = "https://freehire.me"

# freehire asks callers to identify themselves. Nothing behaves differently
# without it - it buys a heads-up before a limit or a field changes, which a
# default library user-agent cannot get you.
default_user_agent = "python-jobspy/freehire (+https://github.com/pa741/JobSpy)"

headers = {
    "Accept": "application/json",
}

# The API clamps rather than rejects, but asking for more than 100 just wastes
# the round trip.
max_page_size = 100

# offset + limit may not exceed this on the job endpoints; past it the API 400s.
max_offset = 10000

job_type_map = {
    JobType.FULL_TIME: "full_time",
    JobType.PART_TIME: "part_time",
    JobType.CONTRACT: "contract",
    JobType.INTERNSHIP: "internship",
}

# freehire's enrichment reports employment type in its own vocabulary; map it
# back onto JobType. "fellowship" has no JobSpy equivalent and is dropped.
employment_type_map = {
    "full_time": JobType.FULL_TIME,
    "part_time": JobType.PART_TIME,
    "contract": JobType.CONTRACT,
    "internship": JobType.INTERNSHIP,
}

salary_period_map = {
    "year": CompensationInterval.YEARLY,
    "month": CompensationInterval.MONTHLY,
    "day": CompensationInterval.DAILY,
    "hour": CompensationInterval.HOURLY,
}

description_format_map = {
    "markdown": "markdown",
    "html": "html",
    "plain": "text",
}

# The three geography facets join into ONE OR-group rather than intersecting,
# so naming two of them widens the search instead of narrowing it. Used to
# detect when the caller has already picked a level for us.
geography_facets = ("regions", "countries", "cities")
