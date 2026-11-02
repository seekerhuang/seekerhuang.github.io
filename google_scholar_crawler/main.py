import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

scholar_id = os.environ['GOOGLE_SCHOLAR_ID']
profile_url = 'https://scholar.google.com/citations?' + urlencode({
    'user': scholar_id, 'hl': 'en', 'pagesize': 100,
})
request = Request(profile_url, headers={'User-Agent': 'Mozilla/5.0'})
with urlopen(request, timeout=30) as response:
    soup = BeautifulSoup(response.read(), 'html.parser')

name = soup.select_one('#gsc_prf_in')
total = soup.select_one('#gsc_rsb_st .gsc_rsb_std')
if name is None or total is None:
    raise RuntimeError('Google Scholar did not return an author profile.')

publications = {}
for row in soup.select('#gsc_a_b .gsc_a_tr'):
    title = row.select_one('.gsc_a_at')
    paper_id = parse_qs(urlsplit(title['href']).query)['citation_for_view'][0]
    count = row.select_one('.gsc_a_ac').get_text(strip=True)
    publications[paper_id] = {
        'author_pub_id': paper_id,
        'bib': {'title': title.get_text(strip=True)},
        'num_citations': int(count.replace(',', '') or '0'),
    }
if not publications:
    raise RuntimeError('Google Scholar did not return the publication list.')

author = {
    'name': name.get_text(strip=True),
    'scholar_id': scholar_id,
    'citedby': int(total.get_text(strip=True).replace(',', '')),
    'publications': publications,
    'updated': datetime.now(timezone.utc).isoformat(),
}
results = Path('results')
results.mkdir(exist_ok=True)
(results / 'gs_data.json').write_text(json.dumps(author, ensure_ascii=False), encoding='utf-8')
(results / 'gs_data_shieldsio.json').write_text(json.dumps({
    'schemaVersion': 1,
    'label': 'citations',
    'message': str(author['citedby']),
}), encoding='utf-8')
print(json.dumps(author, ensure_ascii=False, indent=2))
