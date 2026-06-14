import requests
from bs4 import BeautifulSoup
import json

url = 'https://materdolorosa.cl/noticias/'
response = requests.get(url, verify=False) # In case there are SSL issues
soup = BeautifulSoup(response.content, 'lxml')

# find common article or post containers
articles = soup.find_all('article')
if not articles:
    # maybe they have a different class like '.post'
    articles = soup.select('.post, .blog-post, .news-item')

print(f"Found {len(articles)} articles.")

result = []
for i, article in enumerate(articles[:3]): # just check first 3
    a_tag = article.find('a')
    link = a_tag['href'] if a_tag and a_tag.has_attr('href') else None
    
    img_tag = article.find('img')
    img_src = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
    
    title_tag = article.find(['h1', 'h2', 'h3', 'h4'])
    title = title_tag.get_text(strip=True) if title_tag else None
    
    # Extract excerpt
    p_tags = article.find_all('p')
    excerpt = p_tags[0].get_text(strip=True) if p_tags else None
    
    result.append({
        'index': i,
        'title': title,
        'link': link,
        'img': img_src,
        'excerpt': excerpt
    })

print(json.dumps(result, indent=2, ensure_ascii=False))
