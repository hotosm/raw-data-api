Module API.auth.routers
=======================

Variables
---------

```python3
router
```

Functions
---------

    
#### callback

```python3
def callback(
    request: starlette.requests.Request
)
```
Performs token exchange between OpenStreetMap and Raw Data API 

Core will use Oauth secret key from configuration while deserializing token,
provides access token that can be used for authorized endpoints.

Parameters: None

Returns:
- access_token (string)

    
#### login_url

```python3
def login_url(
    request: starlette.requests.Request
)
```
Generate Login URL for authentication using OAuth2 Application registered with OpenStreetMap.
Click on the download url returned to get access_token.

Parameters: None

Returns:
- login_url (string) - URL to authorize user to the application via. Openstreetmap
    OAuth2 with client_id, redirect_uri, and permission scope as query_string parameters

    
#### my_data

```python3
def my_data(
    user_data: API.auth.AuthUser = Depends(login_required)
)
```
Read the access token and provide  user details from OSM user's API endpoint,
also integrated with underpass .

Parameters:None

Returns: user_data