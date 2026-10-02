Images are stored in `assets/images` and referenced in the markdown using the syntax described below and the path relative to the `assets/` directory. When you add new images, add them to a subdirectory of `assets/images` which is relevant to the document or section you are working on. Create a new subdirectory if you are working on a new document or section.

The preferred method for adding images to the documentation is using the `image.html` shortcode syntax. This method allows you to modify the image size and apply various attributes. If you need to add additional functionality to the image shortcode you can edit `image.html` in the `/layouts/shortcodes/` directory of the repository.

## Formats 

Images can be in JPEG, WEBP, PNG or SVG format. For screen shots, high-resolution PNGs are preferred. For system diagrams, SVG images are preferred. We recommend avoiding JPEG format to maintain image quality. If you are compressing screenshots or vector graphics, it is strongly recommended to convert to WEBP format rather than JPEG.

## Syntax
The minimal syntax to invoke the image shortcode is the following:

```html
{{ < image path="/images/path/to/image.png" > }}
```

Image paths are relative to the `assets/` directory and do not include the `assets/` directory. If you add images, we recommend using folders inside the `/assets/images` directories to group images belonging to the same document or documentation category. 

Mandatory:
* Double enclosing curly brackets
* `< image ... >` tag containing attributes
* `path` attribute containing the path to the image file relative to `assets/`

Optional:
* `alt` - alternative text if image is missing
* `align` - alignment, e.g. "left", "right", "center"
* `width` - image width as a pixel value or percentage
* `mt` - upper margin (useful for keeping distance between text and images)
* `mb` - lower margin (useful for keeping distance between text and images)
* `border` - by default borders are applied to images, set this to "false" to avoid it
* `pathDark` - path to alternative darkmode image option for darkmode documentation

The following example demonstrates how to apply sizing, centering, margin and disable borders:

```html
{{< image path="/images/ISO/00-onepoc_architecture.svg" alt="OnePOC Architecture" align="center" width="80%" mb="20px" border="false" >}}
```

This next example demonstrates how to include images for the dark mode:

```html
{{< image
  pathDark="/images/quickstart/dark/sunstone_login_page.png"
  path="/images/quickstart/light/sunstone_login_page.png"
  alt="Sunstone login" align="center" width="50%" mb="20px"
>}}
```

When including Sunstone screenshots, it is preferred to include the same screenshot in both dark mode and light mode, and store them in respective `dark/` and `light/` subdirectories as demonstrated in the above example

## Legacy Format

The OpenNebula documentation also contains some images included using the default markdown syntax:

```html
![image1](/images/sunstone_user_info_quotas.png)
```

It is recommended to alter images included using the legacy format to the shortcode format detailed above.
