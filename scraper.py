import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from analytics import record_page

def scraper(url, resp):
    if resp.status == 200 and resp.raw_response and resp.raw_response.content:
        record_page(resp.url, resp.raw_response.content)

    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    #checks if the page was recieved
    if resp.status != 200 or not resp.raw_response:
        return []
    
    hyperlinks = set() # Use a set to prevent adding the same link twice per page
    try:
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        for anchor in soup.find_all('a'):
            href = anchor.get('href')
            if href:
                # Resolve relative links (e.g., '/about') into full URLs
                full_url = urljoin(url, href)
                # Requirement: Remove the fragment part of the URL
                clean_url = urldefrag(full_url)[0]
                hyperlinks.add(clean_url)
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")
        
    return list(hyperlinks)

def is_valid(url):
    try:
        if not url or len(url) > 300:
            return False

        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return False
        
        allowed_domains = [".ics.uci.edu", ".cs.uci.edu", 
                           ".informatics.uci.edu", ".stat.uci.edu"]
        if not any(parsed.netloc.endswith(d) for d in allowed_domains):
            return False
        

        # Added .py, .txt, .sas, .odc, .php, and version control files (.ppsx, .odc)
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|thmx|mso|arff|rtf|jar|csv|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|py|sas|odc|txt|ppsx|pps|odc|sas|m|h|cpp|c|java)$", 
            parsed.path.lower()):
            return False
        
        
        # Blocks infinite commit/tree hashes and repeating folders
        if any(x in parsed.path.lower() for x in ['/commit/', '/tree/', '/blob/', '/raw/', '/src/','/pix/']):
            return False
        if re.search(r'(/[^/]+)\1{2,}', parsed.path):
            return False
        if len(parsed.path.split('/')) > 6:
            return False
        # Combined check for query and path to catch shuffled Wiki/Apache params
        trap_params = [
            'action=', 'do=', 'rev=', 'format=', 'timeline=', 'image=', 
            'tab_details=', 'tab_files=', 'ns=', 'share=', 'diff=', 
            'view=', 'day=', 'month=', 'year=', 'idx=', 'c=', 'o=', 'sort='
        ]
        full_url_low = url.lower()
        if any(param in full_url_low for param in trap_params):
            return False

        
        # Blocks known trouble spots like infinite calendars and helpdesks
        if any(keyword in full_url_low for keyword in ["calendar", "wp-content", "login", "helpdesk.ics"]):
            return False
        
        return True

    except Exception as e:
        print(f"Validation error for {url}: {e}")
        return False

