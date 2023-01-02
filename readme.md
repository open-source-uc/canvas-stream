# Canvas-Stream

A [smart](#smart) and [small](#small) python module for downloading
the current favorite courses files from Canvas-LMS.

## Setup

### Installation

Be sure to have python3 downloaded and in PATH.

First, add a `config.toml` file with the canvas `url`
and the API `access_token` (with is usually available at
`${url}/profile/settings#access_tokens`) like this:

```toml
url = 'https://to.canvas.com'
access_token = 'insert-random-chars-here'
```

Then run the following commands:

```ps1
python3 -m venv .venv

# on unix-like system
. .venv/bin/activate
# on Windows
. .\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

Then, run the program with:

```
python -m canvas_stream
```

### Development

Adicionales requirements should be installed:

```ps1
python -m pip install -r requirements.dev.txt
```

> This project uses type annotations, so enable or install [mypy][mypy]
> or other type checker extension (like [pylance][pylance]) to use useful
> suggestions and automatic reporting of errors with types ✨

Before committing, run the following commands:

```bash
black canvas_stream
mypy canvas_stream
pylint canvas_stream  # TODO: add linter config
```

## Notes

<!-- TODO: move this to docs/ -->

### Small

In comparison with other popular canvas files downloaders, like
[canvas_grab][canvas_grab] and [canvasFileSync][canvasFileSync],
this program doesn't have big or a lot of dependencies,
this module has only 2: `request` and `toml`.

The codebase is also small, at around 550 lines of code.

### Smart

It uses a mix of the GraphQL and the REST API with a sqlite3
database cache to fetch only stuff as needed.
After the first run, the fetch iteration should take a second.

Also, if the program is stopped, the next time it will continue
where it left and check additionally if there was an update in
the courses.


### Asome things to implement in the future

- Handle if a file is downloadable or not
- Download multiple files in the same time (async+await, threads poll?)
- Download files from Google Drive (see [`gdown`][gdown])
- Make url / links with common external urls pages (Wikipedia, YouTube, etc)
- Better logging (see [how to `logging`][hotto_logging])
- User configuration
- Better correlation with DB File and filesystem file
- Simple user interface (separated from the core code)
- Guide of how to install `python3` (Windows Store!)
- Guide on how to add the program to PATH, so it could be used everywhere


<!-- links here! -->
[canvas_grab]: https://github.com/skyzh/canvas_grab
[canvasFileSync]: https://github.com/drew-royster/canvasFileSync
[gdown]: https://github.com/wkentaro/gdown
[hotto_logging]: https://docs.python.org/3/howto/logging.html
[mypy]: http://mypy-lang.org/
[pylance]: https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance
