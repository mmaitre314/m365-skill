'''
This sample shows how to download a file from a SharePoint Sharing URL using Microsoft Graph API and Azure Identity.
To run the sample, provide the sharing URL and the path to save the file as command line arguments:
    python download_sharing_url.py <sharing_url> <save_path>
Example:
    python download_sharing_url.py "https://contoso.sharepoint.com/:x:/r/sites/ExampleSite/Shared%20Documents/Example.xlsx?d=1234" "Example.xlsx"
'''

from base64 import urlsafe_b64encode
from sys import argv, platform

import requests
from azure.identity.broker import InteractiveBrowserBrokerCredential

url = argv[1]
path = argv[2]

print("Encoding sharing URL...")

sharing_token = "u!" + urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
print(f"Sharing token: {sharing_token[:100]}...")

print("Authenticating...")

if platform == "win32":
    import win32gui
    window_handle = win32gui.GetForegroundWindow()
else:
    import msal
    window_handle = msal.PublicClientApplication.CONSOLE_WINDOW_HANDLE

credential = InteractiveBrowserBrokerCredential(
    client_id="d3590ed6-52b3-4102-aeff-aad2292ab01c",
    parent_window_handle=window_handle,
    use_default_broker_account=True,
)
access_token = credential.get_token("https://graph.microsoft.com/.default").token
print(f"Access token: {access_token[:100]}...")

print("Downloading file...")

r = requests.get(
    f"https://graph.microsoft.com/v1.0/shares/{sharing_token}/driveItem/content",
    headers={"Authorization": f"Bearer {access_token}"},
)
print(f"Response status code: {r.status_code}, content length: {len(r.content)}")
for r2 in r.history:
    print(f"Redirect from {r2.url[:100]}... with status {r2.status_code}")

with open(path, "wb") as f:
    f.write(r.content)

print(f"File downloaded to {path}")