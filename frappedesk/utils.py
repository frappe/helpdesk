from bs4 import BeautifulSoup
import frappe

def extract_mentions(html):
	print(html)
	if not html:
		return []
	soup = BeautifulSoup(html, 'html.parser')
	mentions = []
	for d in soup.find_all('span', attrs={'class': 'mention'}):
		mentions.append(frappe._dict(email=d.get('data-id')))
	return mentions