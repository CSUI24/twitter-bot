This is the Twitter service for menfess.

### Attach images to tweets

The `POST /api/v1/tweets` endpoint accepts up to four public HTTPS image URLs in
`image_urls`. The service downloads each image (maximum 1 MiB), uploads it to X,
then creates the tweet with the returned media IDs. Supported formats are JPEG,
PNG, WebP, and GIF.

Set `TWITTER_MEDIA_ALLOWED_HOSTS` on this service to the hostname serving your
R2 public bucket. Use only the hostname, without a scheme or path; separate
multiple hosts with commas. For example:

```env
TWITTER_MEDIA_ALLOWED_HOSTS=images.example.com
```

The web app must send image URLs from that same host, such as its configured
`R2_PUBLIC_URL` custom domain. This allowlist prevents the service from making
requests to arbitrary hosts.
