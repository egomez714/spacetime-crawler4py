import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from analytics import record_page

url_pattern_counts = {}

def scraper(url, resp):
    if resp.status == 200 and resp.raw_response and resp.raw_response.content:
        record_page(resp.url, resp.raw_response.content)
    if len(resp.raw_response.content) > 1_000_000:
        return []
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
    if resp.status != 200:
        return []
    else:
        #parses the html content with Beautiful Soup Library 
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        #Empty set to store hyperlinks and remove duplicates
        hyperlinks = set()
        #Finds all the anchor tags <a>, that holds the hyperlinks
        all_links = soup.find_all('a')
        #Goes through each link found on the page
        for value in all_links:
            if value.get('href'):
                #Gets the URL
                href = value.get('href')
                full_url = urljoin(url, href)
                #removes the fragmented part
                full_url = urldefrag(full_url)[0]
                #Adds the URL to the set of hyperlinks
                hyperlinks.add(full_url)
    #Converts the set to a list
    return list(hyperlinks)

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        full_url_low = url.lower()
        path_low = parsed.path.lower()
        # stores allowed domains
        allowed_domains = [".ics.uci.edu", ".cs.uci.edu", 
            ".informatics.uci.edu", ".stat.uci.edu"
            ]
        
        # checks if url is in allowed_domains
        if not any(parsed.netloc.endswith(d) for d in allowed_domains):
            return False
        
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            r"|epub|dll|cnf|tgz|sha1|thmx|mso|arff|rtf|jar|csv|rm|smil|wmv|swf|wma|zip|rar|gz"
            r"|patch|diff|git|ipynb|emx|mpg|scm|ss|rkt|nb|nbp|bib|odp|db|war|dtd|sql|img)$", path_low):
            return False
        
        trap_patterns = [
            # Slide & Presentation Traps (~ziv, ~dsm, etc.)
            r".*/~[a-zA-Z0-9]+/.*(sld|tsld)[0-9]+\.htm.*",
            r".*/~[a-zA-Z0-9]+/(presentations|slides)/.*",
            
            # Wiki maintenance & revisions
            r".*/doku\.php/projects:maint-.*",
            r".*/doku\.php/.*(\?do=diff|\&rev=).*",
            
            # Legacy archives (Pre-2023)
            r".*/~[a-zA-Z0-9]+/(courses|teaching|class|assignments|homeworks|grad/courses)/(19|20[0-2])[0-9].*",
            
            # Recursive publications & technical silos
            r".*/~[a-zA-Z0-9]+/publications/[ar][0-9]+[A-Z]?\.html.*",
            r".*/~[a-zA-Z0-9]+/(papers|softwares|benchmarks|bibs|junkyard)/.*",
            
            # Calendar & Event Loops
            r".*(\?tribe|eventdisplay|ical|outlook-ical|eventdate=).*",
            r".*/events/.*(month|list|tag|page/|today|week).*",
            r".*/events/20[0-2][0-9]-[0-9]{2}.*",
            
            # GitLab & Mailman sinks
            r"^https?://gitlab\.ics\.uci\.edu/.*(/-/|/tags|/branches|/commits|/starrers|/forks|/activity|/users).*",
            r"^https?://mailman\.ics\.uci\.edu/.*",
            
            # Photo galleries and image browsing
            r'.*/gallery/.*(\?|&)(page|image|photo)=.*',
            r'.*/photos/.*[0-9]{3,}.*',
            r'.*/images?/.*[0-9]{3,}.*',
            
            # Pagination traps
            r'.*/page/[0-9]{2,}.*',
            r'.*[\?&]page=[0-9]{2,}.*',
            
            # Date-based archives (can create infinite combinations)
            r'.*/[0-9]{4}/[0-9]{2}/[0-9]{2}.*',
            r'.*/archive/[0-9]{4}.*',
            
            # Search and filter combinations
            r'.*[\?&](filter|sort|order|search|query)=.*',
            
            # Session IDs and tracking parameters
            r'.*[\?&](session|sid|token|key|PHPSESSID)=.*',
            
            # PDF viewers and document processors
            r'.*/pdfviewer.*',
            r'.*[\?&](view|viewer|display)=.*',
            
            # Printer-friendly and share versions
            r'.*[\?&](print|share|format)=.*',
            
            # Comment and reply chains
            r'.*[\?&](replytocom|comment)=.*',
            
            # Version control and diff pages
            r'.*/diff/.*',
            r'.*/compare/.*',
        ]
        for pattern in trap_patterns:
            if re.search(pattern, full_url_low):
                return False
        
        # catches repeating directories /abc/abc/abc
        if re.search(r'(/.+?)\1{2,}', path_low):
            return False
        

        # Detect path depth (prevent extremely deep paths)
        path_segments = [p for p in parsed.path.split('/') if p]
        if len(path_segments) > 15:  # Maximum depth limit
            return False
        
        # Detect too many duplicate segments in path
        if len(path_segments) > 0 and len(path_segments) > len(set(path_segments)) + 3:
            return False
        
        # Check URL length
        if len(url) > 200:
            return False
        
        # checks for infinite filter combinations
        if url.count("?") > 1 or url.count("&") > 5:
            return False
        
        
        # Avoid wiki diff/history/edit pages - low information content
        if re.search(r'\?.*do=(diff|history|edit|old|view|revisions)', parsed.query.lower()):
            return False
        
        # Avoid pages with array-like parameters

        if re.search(r'\[\d+\]', parsed.query):
            return False
        
        # Avoid excessive query parameters that indicate wiki traps
        if url.count("[") >= 2 or url.count("]") >= 2:
            return False
        # Track URL patterns to detect traps (removing numbers to find patterns)
        pattern = re.sub(r'\d+', 'N', url)
        url_pattern_counts[pattern] = url_pattern_counts.get(pattern, 0) + 1
        
        # If we've seen this pattern too many times, it's likely a trap
        if url_pattern_counts[pattern] > 30:
            return False
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        return False
