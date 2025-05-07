import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# =========================================
# Crawl and Save Full Site with Monolith
# =========================================
# Author: Cyril Wolfangel
# =========================================

def save_page(url, output_dir):
    # Parse the URL path and create subdirectories if needed
    parsed_path = urlparse(url).path.strip('/')
    if not parsed_path:  # Handle root URLs
        parsed_path = 'index.html'
    else:
        if not parsed_path.endswith('.html'):
            parsed_path += '.html'

    # Create the relative destination path
    relative_destination = os.path.join(output_dir, parsed_path.replace('/', os.sep))
    os.makedirs(os.path.dirname(relative_destination), exist_ok=True)  # Ensure subdirectories exist

    # Convert the relative path to a format suitable for the `-o` parameter
    relative_destination_for_monolith = os.path.relpath(relative_destination, start=os.getcwd())

    print(f"Capturing URL: {url}")
    print(f"To Local: {relative_destination_for_monolith}")
    
    # Construct the monolith command with the relative path
    monolith_command = f"monolith {url} -e -o {relative_destination_for_monolith}"
    
    # Echo the command with extra newlines for visibility
    print("\n\n" + monolith_command + "\n\n")
    
    # Execute the monolith command
    os.system(monolith_command)

def adjust_links_in_file(filepath, base_url):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        # Remove <base> tag if present
        base_tag = soup.find('base')
        if base_tag:
            base_tag.decompose()

        # Extract the "per-site" folder name from the base URL
        url_parts = urlparse(base_url)
        base_folder = url_parts.netloc.replace('.', '_')

        for tag in soup.find_all(['a', 'img', 'link', 'script']):
            attr = 'href' if tag.name in ['a', 'link'] else 'src'
            if tag.has_attr(attr):
                original_url = tag[attr]
                if original_url.startswith(base_url):
                    parsed_url = urlparse(original_url)
                    if parsed_url.path and parsed_url.path.strip('/'):
                        # Convert to absolute path including the "per-site" folder
                        absolute_path = os.path.join(
                            os.getcwd(), base_folder, parsed_url.path.strip('/')
                        ).replace('\\', '/')
                        absolute_path = f"file:///{absolute_path}"
                        tag[attr] = absolute_path

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(str(soup))
        print(f"Adjusted links in {filepath}")
    except Exception as e:
        print(f"Failed to adjust links in {filepath}: {e}")

def crawl(url, base_url, output_dir, max_pages):
    if max_pages > 0 and len(visited) >= max_pages:
        return
    if url in visited:
        return
    visited.add(url)
    print(f"Crawling: {url}")
    save_page(url, output_dir)
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        for link in soup.find_all('a', href=True):
            next_url = urljoin(base_url, link['href'])
            if base_url in next_url and next_url not in visited:
                crawl(next_url, base_url, output_dir, max_pages)
    except Exception as e:
        print(f"Failed to crawl {url}: {e}")

def adjust_all_links(output_dir, base_url):
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                adjust_links_in_file(filepath, base_url)

if __name__ == "__main__":
    base_url = input("Enter the URL of your site: ").strip()
    max_pages = int(input("Enter the maximum number of pages to crawl (0 for no limit): ").strip())
    
    # Create output directory based on base URL
    url_parts = urlparse(base_url)
    base_dir_name = url_parts.netloc.replace('.', '_')
    output_dir = os.path.join(os.getcwd(), base_dir_name)
    os.makedirs(output_dir, exist_ok=True)
    
    visited = set()
    crawl(base_url, base_url, output_dir, max_pages)
    adjust_all_links(output_dir, base_url)
