"""WordPress Publisher Utility for publishing HTML websites to WordPress"""

import requests
import re
from urllib.parse import urljoin
from typing import Dict, Optional, List
import os
import base64

class WordPressPublisher:
    """Handle publishing HTML websites to WordPress via REST API"""
    
    def __init__(self, wp_url: str, wp_username: str, wp_password: str, use_cookie_auth: bool = False):
        """
        Initialize WordPress publisher
        
        Args:
            wp_url: WordPress site URL (e.g., https://wordpress.apexneural.cloud)
            wp_username: WordPress username
            wp_password: WordPress application password or user password
            use_cookie_auth: If True, use cookie-based authentication (requires login first)
                           If False, use Basic Auth with Application Passwords (recommended for external access)
        """
        self.wp_url = wp_url.rstrip('/')
        self.wp_api_url = f"{self.wp_url}/wp-json/wp/v2"
        self.wp_username = wp_username
        self.wp_password = wp_password
        self.use_cookie_auth = use_cookie_auth
        self.session = requests.Session()
        self.wp_nonce = None  # Will be set during cookie login if needed
        
        # Create Authorization header for WordPress REST API
        # WordPress REST API uses Basic Auth with base64 encoded username:password
        # For WordPress 5.6+, use Application Passwords (not regular passwords)
        # Application Passwords can be created at: wp-admin -> Users -> Edit User -> Application Passwords
        credentials = f"{wp_username}:{wp_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
        
        # If using cookie auth, login first
        # Note: Cookie auth works best within WordPress. For external API access, use Application Passwords
        if use_cookie_auth:
            print("[LOG] Using cookie-based authentication (may not work for external API access)")
            self._login_with_cookies()
        else:
            print("[LOG] Using Basic Authentication with Application Password (recommended for external access)")
    
    def _login_with_cookies(self) -> bool:
        """
        Login to WordPress using cookie-based authentication
        This requires getting a nonce token from WordPress admin area
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Step 1: Get login page to extract any required nonces
            login_url = f"{self.wp_url}/wp-login.php"
            response = self.session.get(login_url, timeout=10)
            
            # Extract login form nonce if present (WordPress sometimes requires it)
            login_nonce = None
            if response.status_code == 200:
                content = response.text
                # Look for login form nonce
                nonce_match = re.search(r'name=["\']_wpnonce["\']\s+value=["\']([^"\']+)["\']', content)
                if nonce_match:
                    login_nonce = nonce_match.group(1)
                    print(f"[LOG] Found login form nonce: {login_nonce[:10]}...")
            
            # Step 2: Prepare login form data
            login_data = {
                'log': self.wp_username,
                'pwd': self.wp_password,
                'wp-submit': 'Log In',
                'redirect_to': f"{self.wp_url}/wp-admin/",
                'testcookie': '1'
            }
            
            # Add nonce if found
            if login_nonce:
                login_data['_wpnonce'] = login_nonce
            
            # Step 3: Perform login with proper headers
            headers = {
                'Referer': login_url,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = self.session.post(
                login_url, 
                data=login_data, 
                headers=headers,
                timeout=10, 
                allow_redirects=False  # Don't follow redirects, check status code
            )
            
            # Check if login was successful (WordPress redirects on success)
            login_success = False
            if response.status_code in [302, 301, 200]:
                # Check for authentication cookies
                cookies_str = str(self.session.cookies)
                if 'wordpress_logged_in' in self.session.cookies or 'wordpress_' in cookies_str:
                    login_success = True
                    print(f"[LOG] Login successful - Status: {response.status_code}")
                    print(f"[LOG] Cookies found: {list(self.session.cookies.keys())}")
                elif response.status_code == 302:
                    # Might be redirecting, check Location header
                    location = response.headers.get('Location', '')
                    if 'wp-admin' in location or 'dashboard' in location.lower():
                        login_success = True
                        print(f"[LOG] Login successful - Redirecting to: {location}")
            
            if not login_success:
                # Check if there's an error message
                if response.status_code == 200:
                    error_match = re.search(r'class=["\'](login-error|message)["\'][^>]*>([^<]+)', response.text)
                    if error_match:
                        print(f"[ERROR] Login error: {error_match.group(2)}")
                print(f"[ERROR] Login failed - Status: {response.status_code}")
                print(f"[ERROR] Response headers: {dict(response.headers)}")
                return False
            
            # Step 4: Follow redirect if needed to establish session
            if response.status_code in [302, 301]:
                redirect_url = response.headers.get('Location', '')
                if redirect_url:
                    if not redirect_url.startswith('http'):
                        redirect_url = f"{self.wp_url}{redirect_url}"
                    print(f"[LOG] Following redirect to: {redirect_url}")
                    self.session.get(redirect_url, timeout=10)
            
            # Verify we have cookies after redirect
            if 'wordpress_logged_in' in self.session.cookies or 'wordpress_' in str(self.session.cookies):
                print("[LOG] Successfully logged in to WordPress with cookies")
                
                # Step 5: Get REST API nonce from WordPress
                # WordPress REST API requires a nonce for cookie authentication
                # The nonce can be found in wpApiSettings or retrieved via a REST API call
                nonce = None
                
                # Method 1: Try to get nonce from wp-admin page
                # The nonce must be for 'wp_rest' action (see WordPress REST API documentation)
                admin_url = f"{self.wp_url}/wp-admin/"
                response = self.session.get(admin_url, timeout=10)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Look for wpApiSettings.nonce in JavaScript with multiple patterns
                    # WordPress creates nonce with: wp_create_nonce('wp_rest')
                    # This is found in wpApiSettings object
                    patterns = [
                        r'wpApiSettings\s*=\s*\{[^}]*"nonce"\s*:\s*["\']([a-zA-Z0-9]{10,})["\']',  # wpApiSettings = {"nonce":"..."}
                        r'wpApiSettings\s*=\s*\{[^}]*nonce["\']:\s*["\']([a-zA-Z0-9]{10,})["\']',  # wpApiSettings = {nonce:"..."}
                        r'wp\.apiFetch\.defaults\s*=\s*\{[^}]*"nonce"\s*:\s*["\']([a-zA-Z0-9]{10,})["\']',  # wp.apiFetch.defaults
                        r'var\s+wpApiSettings\s*=\s*\{[^}]*"nonce"\s*:\s*["\']([a-zA-Z0-9]{10,})["\']',  # var wpApiSettings
                        r'window\.wpApiSettings\s*=\s*\{[^}]*"nonce"\s*:\s*["\']([a-zA-Z0-9]{10,})["\']',  # window.wpApiSettings
                        r'wpApiSettings\s*=\s*\{[^\}]+nonce["\']?\s*:\s*["\']([a-zA-Z0-9]{10,})["\']',  # More flexible pattern
                    ]
                    
                    for pattern in patterns:
                        nonce_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                        if nonce_match:
                            potential_nonce = nonce_match.group(1)
                            # WordPress nonces are typically 10 characters long, alphanumeric
                            if len(potential_nonce) >= 10:
                                nonce = potential_nonce
                                print(f"[LOG] Found nonce using pattern: {pattern[:50]}...")
                                break
                
                # Method 2: Try to get nonce from admin-ajax.php
                if not nonce:
                    try:
                        ajax_url = f"{self.wp_url}/wp-admin/admin-ajax.php"
                        # WordPress admin-ajax might return nonce in response
                        ajax_response = self.session.get(ajax_url, timeout=10)
                        if ajax_response.status_code == 200:
                            ajax_content = ajax_response.text
                            nonce_match = re.search(r'["\']nonce["\']:\s*["\']([^"\']+)["\']', ajax_content)
                            if nonce_match:
                                nonce = nonce_match.group(1)
                    except:
                        pass
                
                # Method 3: Try to get nonce from REST API endpoint (WordPress provides it when logged in)
                if not nonce:
                    try:
                        # Try to get nonce from REST API root - WordPress provides it when authenticated
                        rest_url = f"{self.wp_url}/wp-json/"
                        rest_response = self.session.get(rest_url, timeout=10, headers={'Accept': 'application/json'})
                        
                        # Check headers first
                        if 'X-WP-Nonce' in rest_response.headers:
                            nonce = rest_response.headers['X-WP-Nonce']
                            print(f"[LOG] Found nonce in REST API header: {nonce[:20]}...")
                        else:
                            # Try to parse JSON response - sometimes nonce is in the response
                            try:
                                rest_data = rest_response.json()
                                if isinstance(rest_data, dict) and 'nonce' in rest_data:
                                    nonce = rest_data['nonce']
                            except:
                                pass
                            
                            # Also check response body for nonce
                            if not nonce and rest_response.status_code == 200:
                                content = rest_response.text
                                nonce_match = re.search(r'["\']nonce["\']:\s*["\']([a-f0-9]{10,})["\']', content)
                                if nonce_match:
                                    nonce = nonce_match.group(1)
                    except Exception as e:
                        print(f"[WARN] Error getting nonce from REST API: {e}")
                        pass
                
                if nonce:
                    self.wp_nonce = nonce
                    print(f"[LOG] Retrieved WordPress nonce: {nonce[:20]}...")
                    return True
                else:
                    # Try one more method: Visit edit.php to get nonce (WordPress admin pages have it)
                    try:
                        edit_url = f"{self.wp_url}/wp-admin/edit.php"
                        edit_response = self.session.get(edit_url, timeout=10)
                        if edit_response.status_code == 200:
                            edit_content = edit_response.text
                            import re
                            # Look for wpApiSettings in edit page
                            nonce_match = re.search(r'wpApiSettings\s*=\s*\{[^}]*"nonce"\s*:\s*["\']([^"\']+)["\']', edit_content, re.DOTALL)
                            if nonce_match:
                                nonce = nonce_match.group(1)
                                self.wp_nonce = nonce
                                print(f"[LOG] Retrieved WordPress nonce from edit page: {nonce[:20]}...")
                                return True
                    except:
                        pass
                    
                    print("[WARN] Could not extract nonce. WordPress REST API requires nonce for cookie authentication.")
                    print("[WARN] Attempting to continue without nonce - this may fail.")
                    self.wp_nonce = None
                    return True
            else:
                print(f"[WARN] Cookie login failed: No authentication cookies set")
                return False
                
        except Exception as e:
            print(f"[ERROR] Cookie login error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_auth_headers(self) -> Dict:
        """
        Get authentication headers based on auth method
        
        Returns:
            Dict of headers for authentication
        """
        if self.use_cookie_auth:
            # Cookie auth needs nonce in X-WP-Nonce header
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            if self.wp_nonce:
                headers["X-WP-Nonce"] = self.wp_nonce
                print(f"[LOG] Using nonce in headers: {self.wp_nonce[:20]}...")
            else:
                print("[WARN] No nonce available for REST API request")
            # Cookies are sent automatically by the session
            print(f"[LOG] Cookies in session: {list(self.session.cookies.keys())}")
            return headers
        else:
            return {
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
    
    def test_connection(self) -> Dict:
        """
        Test WordPress API connection and authentication
        
        Returns:
            Dict with success status and message
        """
        try:
            # Test by getting current user info
            endpoint = f"{self.wp_api_url}/users/me"
            headers = self._get_auth_headers()
            
            # Use session if cookie auth, otherwise use requests directly
            if self.use_cookie_auth:
                response = self.session.get(endpoint, headers=headers, timeout=10)
            else:
                response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "success": True,
                    "message": f"Successfully authenticated as {user_data.get('name', 'Unknown')}",
                    "user": user_data
                }
            else:
                return {
                    "success": False,
                    "message": f"Authentication failed: {response.status_code} - {response.text[:200]}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}"
            }
    
    def upload_image(self, image_data: bytes, filename: str, mime_type: str = "image/jpeg") -> Dict:
        """
        Upload image to WordPress media library
        
        Args:
            image_data: Image file bytes
            filename: Original filename
            mime_type: MIME type (image/jpeg, image/png, etc.)
        
        Returns:
            WordPress media object with URL and ID
        """
        endpoint = f"{self.wp_api_url}/media"
        
        # Get base auth headers (without Content-Type, we'll set it for binary data)
        base_headers = self._get_auth_headers()
        
        # For media upload, we need specific headers
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": mime_type
        }
        # Merge auth headers but keep our Content-Type
        for key, value in base_headers.items():
            if key != "Content-Type":  # Don't override Content-Type
                headers[key] = value
        
        try:
            print(f"[LOG] Uploading image to WordPress: {filename} ({len(image_data)} bytes, {mime_type})")
            
            # Use session if cookie auth, otherwise use requests directly
            if self.use_cookie_auth:
                response = self.session.post(
                    endpoint,
                    data=image_data,
                    headers=headers,
                    timeout=120 # Increased timeout for image upload to 120 seconds
                )
            else:
                response = requests.post(
                    endpoint,
                    data=image_data,
                    headers=headers,
                    timeout=120, # Increased timeout for image upload to 120 seconds
                    auth=(self.wp_username, self.wp_password) if not self.use_cookie_auth else None
                )
            
            print(f"[LOG] Image upload response status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                print(f"[ERROR] Image upload failed: {response.status_code}")
                print(f"[ERROR] Response: {response.text[:500]}")
            
            response.raise_for_status()
            media_data = response.json()
            
            print(f"[LOG] Image uploaded successfully - Media ID: {media_data.get('id')}, URL: {media_data.get('source_url', media_data.get('url', 'N/A'))}")
            
            return media_data
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to upload image {filename}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response status: {e.response.status_code}")
                print(f"[ERROR] Response body: {e.response.text[:500]}")
            raise
    
    def upload_image_from_url(self, image_url: str, backend_base_url: str = "") -> Optional[Dict]:
        """
        Upload image from URL to WordPress
        
        Args:
            image_url: Image URL (can be relative or absolute)
            backend_base_url: Base URL for backend (to resolve relative paths)
        
        Returns:
            WordPress media object or None if failed
        """
        try:
            # Resolve relative URLs
            if image_url.startswith('/static/'):
                full_url = f"{backend_base_url}{image_url}"
            elif image_url.startswith('http://') or image_url.startswith('https://'):
                full_url = image_url
            elif image_url.startswith('../static/'):
                full_url = f"{backend_base_url}{image_url.replace('../', '/')}"
            elif '/static/' in image_url:
                # Handle paths like "some/path/static/image.png"
                if image_url.startswith('/'):
                    full_url = f"{backend_base_url}{image_url}"
                else:
                    full_url = f"{backend_base_url}/{image_url}"
            else:
                full_url = f"{backend_base_url}/{image_url}"
            
            print(f"[LOG] Fetching image from: {full_url}")
            
            # Fetch image with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(full_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Get image data
            image_data = response.content
            print(f"[LOG] Image fetched: {len(image_data)} bytes")
            
            # Determine MIME type from content-type or extension
            content_type = response.headers.get('content-type', 'image/jpeg')
            if 'image/png' in content_type:
                mime_type = 'image/png'
                ext = '.png'
            elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
                mime_type = 'image/jpeg'
                ext = '.jpg'
            elif 'image/gif' in content_type:
                mime_type = 'image/gif'
                ext = '.gif'
            elif 'image/webp' in content_type:
                mime_type = 'image/webp'
                ext = '.webp'
            else:
                # Try to determine from filename extension
                url_lower = image_url.lower()
                if url_lower.endswith('.png'):
                    mime_type = 'image/png'
                    ext = '.png'
                elif url_lower.endswith('.gif'):
                    mime_type = 'image/gif'
                    ext = '.gif'
                elif url_lower.endswith('.webp'):
                    mime_type = 'image/webp'
                    ext = '.webp'
                else:
                    mime_type = 'image/jpeg'
                    ext = '.jpg'
            
            # Extract filename
            filename = os.path.basename(image_url)
            # Remove query parameters if any
            filename = filename.split('?')[0]
            if not filename or '.' not in filename:
                filename = f"image_{hash(image_url) % 10000}{ext}"
            elif not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                # Add extension if missing
                filename = f"{filename}{ext}"
            
            print(f"[LOG] Uploading image to WordPress media library: {filename} ({mime_type})")
            
            # Upload to WordPress media library (like n8n reference: POST to /wp-json/wp/v2/media with binary data)
            media_result = self.upload_image(image_data, filename, mime_type)
            return media_result
            
        except Exception as e:
            print(f"[ERROR] Failed to upload image from URL {image_url}: {e}")
            return None
    
    def publish_html_website(self, html_content: str, title: str, 
                            image_url_mapping: Dict[str, str] = None,
                            categories: List[int] = None,
                            tags: List[int] = None,
                            status: str = "publish") -> Dict:
        """
        Publish HTML website to WordPress as a post
        
        Args:
            html_content: Complete HTML content
            title: Post title
            image_url_mapping: Dict mapping old image URLs to new WordPress URLs
            categories: List of category IDs (default: [33])
            tags: List of tag IDs (default: [34])
            status: Post status (default: "publish")
        
        Returns:
            Published post data with URL and ID
        """
        # Replace image URLs if provided
        # Need to replace all variations: absolute URLs, relative URLs, and in different contexts
        if image_url_mapping:
            print(f"[LOG] Replacing {len(image_url_mapping)} image URLs in HTML...")
            import re
            
            # Build comprehensive replacement map with all URL variations
            replacement_map = {}
            for old_url, new_url in image_url_mapping.items():
                # Add exact match
                replacement_map[old_url] = new_url
                
                # Extract path variations
                old_path = old_url
                if '://' in old_url:
                    try:
                        # Extract path after domain
                        parts = old_url.split('://', 1)[1].split('/', 1)
                        if len(parts) > 1:
                            old_path = '/' + parts[1]
                        else:
                            old_path = '/'
                    except:
                        old_path = old_url
                elif old_url.startswith('/'):
                    old_path = old_url
                elif old_url.startswith('../'):
                    old_path = old_url.replace('../', '/')
                
                # Map all variations
                if old_path != old_url and old_path not in replacement_map:
                    replacement_map[old_path] = new_url
                if old_path.startswith('/') and old_path[1:] not in replacement_map:
                    replacement_map[old_path[1:]] = new_url
            
            # Perform replacements in order (longest first to avoid partial matches)
            sorted_urls = sorted(replacement_map.keys(), key=len, reverse=True)
            
            for old_url in sorted_urls:
                new_url = replacement_map[old_url]
                
                # Replace exact matches (multiple passes to catch all)
                html_content = html_content.replace(old_url, new_url)
                
                # Replace in src="..." or src='...' attributes
                html_content = re.sub(
                    r'(src=["\'])' + re.escape(old_url) + r'(["\'])',
                    r'\1' + new_url + r'\2',
                    html_content,
                    flags=re.IGNORECASE
                )
                
                # Replace in CSS url() functions - handle all quote variations
                html_content = re.sub(
                    r'url\(["\']?' + re.escape(old_url) + r'["\']?\)',
                    f'url("{new_url}")',
                    html_content,
                    flags=re.IGNORECASE
                )
                
                # Replace in background-image
                html_content = re.sub(
                    r'(background-image\s*:\s*url\(["\']?)' + re.escape(old_url) + r'(["\']?\))',
                    r'\1' + new_url + r'\2',
                    html_content,
                    flags=re.IGNORECASE
                )
                
                # Replace in style attributes
                html_content = re.sub(
                    r'(style=["\'][^"\']*url\(["\']?)' + re.escape(old_url) + r'(["\']?\)[^"\']*["\'])',
                    lambda m: m.group(1) + new_url + m.group(2),
                    html_content,
                    flags=re.IGNORECASE
                )
            
            print(f"[LOG] Image URL replacement completed - replaced {len(replacement_map)} URL variations")
            
            # Verify replacements - check for any remaining old URLs
            print(f"[LOG] Verifying URL replacements...")
            remaining_old_urls = []
            for old_url, new_url in image_url_mapping.items():
                # Check if old URL still exists (but allow if it's a substring of new URL)
                if old_url in html_content and old_url not in new_url:
                    remaining_old_urls.append(old_url)
                if new_url in html_content:
                    print(f"[LOG] ✓ WordPress URL found: {new_url[:60]}...")
            
            if remaining_old_urls:
                print(f"[WARN] {len(remaining_old_urls)} old URLs still found in HTML:")
                for url in remaining_old_urls[:5]:  # Show first 5
                    print(f"[WARN]   - {url[:80]}")
            
            # Also do a final pass to catch any missed image URLs
            # Find all image URLs still in HTML and try to replace them
            import re
            # More comprehensive pattern to find all image references
            # Use non-capturing groups for file extensions to avoid tuple issues
            remaining_img_patterns = [
                (r'src=["\']([^"\']+\.(?:png|jpg|jpeg|gif|webp|svg))', 'src'),  # src="..."
                (r'url\(["\']?([^"\')]+\.(?:png|jpg|jpeg|gif|webp|svg))', 'url'),  # url(...)
                (r'background-image\s*:\s*url\(["\']?([^"\')]+\.(?:png|jpg|jpeg|gif|webp|svg))', 'bg'),  # background-image: url(...)
                (r'<img[^>]+src=["\']([^"\']+\.(?:png|jpg|jpeg|gif|webp|svg))', 'img'),  # <img src="..."
            ]
            
            for pattern, pattern_type in remaining_img_patterns:
                remaining_imgs = re.findall(pattern, html_content, re.IGNORECASE)
                if remaining_imgs:
                    print(f"[LOG] Found {len(remaining_imgs)} image references with {pattern_type} pattern")
                    for match in remaining_imgs[:10]:  # Show first 10
                        # Handle both tuple results (from groups) and string results
                        if isinstance(match, tuple):
                            img_url = match[0]  # First capture group is the URL
                        else:
                            img_url = match
                        
                        if img_url and img_url not in [new_url for new_url in image_url_mapping.values()]:
                            print(f"[LOG]   Checking: {img_url[:80]}")
                            # Check if this URL matches any of our uploaded images by filename
                            for old_url, new_url in image_url_mapping.items():
                                # Extract just the filename
                                old_filename = old_url.split('/')[-1].split('?')[0].lower()
                                img_filename = img_url.split('/')[-1].split('?')[0].lower()
                                
                                # Match by filename (case-insensitive)
                                if old_filename == img_filename and img_url != new_url:
                                    # Replace this variation - be careful with regex
                                    html_content = html_content.replace(img_url, new_url)
                                    print(f"[LOG] ✓ Replaced filename match: {img_url[:60]}... -> {new_url[:60]}...")
                                    break
                                
                                # Also try partial match (in case paths differ)
                                if old_filename in img_url or img_filename in old_url:
                                    # More careful replacement for partial matches
                                    if img_url in html_content:
                                        html_content = html_content.replace(img_url, new_url)
                                        print(f"[LOG] ✓ Replaced partial match: {img_url[:60]}... -> {new_url[:60]}...")
                                        break
            
            # Final verification: find all remaining image URLs that might be local
            # Pattern: (attribute, path, folder, extension)
            final_check_pattern = r'(src|href|url\(["\']?)=["\']?([^"\')]*/(static|generated|uploads|media)/[^"\')]+\.(png|jpg|jpeg|gif|webp|svg))'
            final_matches = re.findall(final_check_pattern, html_content, re.IGNORECASE)
            if final_matches:
                print(f"[WARN] Found {len(final_matches)} potential local image URLs that may need replacement:")
                for match in final_matches[:10]:
                    # match is a tuple: (attribute, path, folder, extension)
                    img_path = match[1] if isinstance(match, tuple) and len(match) > 1 else match
                    print(f"[WARN]   - {img_path[:100]}")
                    
                    # Try to find matching image in our mapping by filename
                    img_filename = img_path.split('/')[-1].split('?')[0].lower() if img_path else ""
                    if img_filename:
                        for old_url, new_url in image_url_mapping.items():
                            old_filename = old_url.split('/')[-1].split('?')[0].lower()
                            if old_filename == img_filename:
                                # Replace this local path - handle both quoted and unquoted versions
                                html_content = html_content.replace('"' + img_path + '"', '"' + new_url + '"')
                                html_content = html_content.replace("'" + img_path + "'", "'" + new_url + "'")
                                html_content = html_content.replace(img_path, new_url)
                                print(f"[LOG] ✓ Replaced final check match: {img_path[:60]}... -> {new_url[:60]}...")
                                break
        
        # Default categories and tags
        if categories is None:
            categories = [33]
        if tags is None:
            tags = [34]
        
        # Preserve inline CSS and ensure WordPress doesn't strip style tags
        # WordPress may strip <style> tags, so we need to ensure they're preserved
        # Method 1: Wrap in Gutenberg HTML block (preserves raw HTML)
        # Method 2: Ensure style tags are properly formatted
        # Method 3: Add CSS via inline styles where possible
        
        # Extract and preserve all <style> tags
        style_tags = []
        style_pattern = r'<style[^>]*>.*?</style>'
        style_matches = re.findall(style_pattern, html_content, re.DOTALL | re.IGNORECASE)
        for style_match in style_matches:
            style_tags.append(style_match)
        
        print(f"[LOG] Found {len(style_tags)} <style> tag(s) in HTML")

        layout_css = """
<style id="ai-generated-layout" type="text/css">
html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
    background: none !important;
}
#page, .site, .site-content, .site-main, .site-container, .site-wrapper,
.wp-site-blocks, .wp-block-post-content, .wp-block-group, .wp-block-group__inner-container,
.entry-content, .entry-content > *, .content-area, .page-content, article, .post, .post-content,
.main-wrapper, .page-wrapper, .entry-wrapper, .entry-container {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background: none !important;
    border: 0 !important;
    box-shadow: none !important;
}
body.single, body.single-post, body.page {
    margin: 0 !important;
    padding: 0 !important;
}
.wp-block-spacer, .site-header, .entry-header, .entry-footer,
.post-navigation, .navigation, .comments-area {
    display: none !important;
}
</style>
"""

        css_injected = False
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', '<head>' + layout_css, 1)
            css_injected = True
            print("[LOG] Injected layout CSS after <head>")
        elif re.search(r'<head[^>]*>', html_content, re.IGNORECASE):
            html_content = re.sub(r'<head[^>]*>', lambda m: m.group(0) + layout_css, html_content, count=1, flags=re.IGNORECASE)
            css_injected = True
            print("[LOG] Injected layout CSS after formatted <head>")
        elif '</body>' in html_content:
            html_content = html_content.replace('</body>', layout_css + '</body>', 1)
            css_injected = True
            print("[LOG] Injected layout CSS before </body>")
        else:
            html_content = layout_css + html_content
            css_injected = True
            print("[LOG] Prepended layout CSS (fallback)")

        # Pass the generated HTML straight through without injecting extra styling
        # Wrap in a Gutenberg HTML block to preserve raw markup
        if '<!-- wp:' not in html_content and '<!-- /wp:' not in html_content:
            html_content = '<!-- wp:html -->\n' + html_content + '\n<!-- /wp:html -->'

        print(f"[LOG] HTML content length: {len(html_content)} characters")
        print(f"[LOG] HTML contains <style>: {'<style' in html_content}")
        print(f"[LOG] HTML contains <img>: {'<img' in html_content}")
        print(f"[LOG] HTML contains Gutenberg blocks: {'<!-- wp:' in html_content}")
        
        # Create and publish post
        # WordPress may filter HTML content, so we need to ensure it's preserved
        endpoint = f"{self.wp_api_url}/posts"
        post_data = {
            "title": title,
            "content": html_content,
            "status": status,
            "categories": categories,
            "tags": tags,
            # Ensure content is not filtered - WordPress may strip certain tags
            "format": "standard"  # Use standard format to preserve HTML
        }
        
        headers = self._get_auth_headers()
        
        try:
            # Use session if cookie auth, otherwise use requests directly
            if self.use_cookie_auth:
                response = self.session.post(
                    endpoint,
                    json=post_data,
                    headers=headers,
                    timeout=30
                )
            else:
                response = requests.post(
                    endpoint,
                    json=post_data,
                    headers=headers,
                    timeout=30
                )
            
            # Log response details for debugging
            print(f"[LOG] WordPress API Response Status: {response.status_code}")
            if response.status_code != 200 and response.status_code != 201:
                print(f"[ERROR] WordPress API Error Response: {response.text[:500]}")
            
            response.raise_for_status()
            post_data = response.json()
            
            # Get post URL
            post_url = post_data.get('link', '')
            if not post_url:
                # Construct URL from slug
                slug = post_data.get('slug', '')
                if slug:
                    post_url = f"{self.wp_url}/{slug}"
            
            return {
                "success": True,
                "postId": post_data.get('id'),
                "postUrl": post_url,
                "postData": post_data
            }
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to publish post: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response status: {e.response.status_code}")
                print(f"[ERROR] Response body: {e.response.text[:500]}")
            raise

