import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

def scraper(url, resp):
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
        
        # stores allowed domains
        allowed_domains = [".ics.uci.edu", ".cs.uci.edu", 
            ".informatics.uci.edu", ".stat.uci.edu"
            ]
        
        # checks if url is in allowed_domains
        if not any(parsed.netloc.endswith(d) for d in allowed_domains):
            return False
        
        if  re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        
        # --- TRAP DETECTION ---
        # catches repeating directories /abc/abc/abc
        if re.search(r'(/.+?)\1{2,}',parsed.path):
            return True
        
        # checks URL length
        if len(url) > 200:
            return False
        
        # checks for infinite filter combinations
        if url.count("?") > 1 or url.count("&") > 5:
            return False
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
