# How to Add Notes/Blog Posts

This guide explains how to create, render, and publish notes (blog posts) in Soseki using Jupyter notebooks.

## Overview

Soseki's note/blog system allows you to write content as Jupyter notebooks and automatically convert them to HTML for display on your website. The system:

1. Stores notebooks in the `jup/` directory
2. Converts them to HTML using `jupyter nbconvert`
3. Stores rendered HTML in `app/html/local/notes/`
4. Tracks metadata in `app/html/local/notes/meta.csv`
5. Displays notes via the `/blog/<note>` route

## Directory Structure

```
soseki/
├── jup/                             # Source Jupyter notebooks
│   ├── test.ipynb                   # Example notebook
│   └── your-note.ipynb              # Your new notebook
├── app/
│   └── html/
│       └── local/
│           └── notes/               # Rendered HTML files
│               ├── meta.csv         # Metadata index
│               ├── test.html        # Rendered from test.ipynb
│               └── your-note.html   # Rendered from your-note.ipynb
└── scripts/
    └── render_jup.sh                # Conversion script
```

## Step 1: Create Your Jupyter Notebook

1. **Create a new notebook** in the `jup/` directory:
   ```bash
   cd jup/
   jupyter notebook
   ```

2. **Name your notebook** using a URL-friendly name (lowercase, hyphens, no spaces):
   - ✅ Good: `my-first-post.ipynb`, `data-analysis-2024.ipynb`
   - ❌ Bad: `My First Post.ipynb`, `data analysis.ipynb`

3. **Write your content** using:
   - Markdown cells for text, headers, images
   - Code cells for Python code, data analysis, visualizations
   - Output will be included in the rendered HTML

4. **Save your notebook** when complete

### Example Notebook Structure

```python
# Cell 1: Markdown
# My Blog Post Title

This is an introduction to my post.

## Section 1

Content goes here...

# Cell 2: Code
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.plot(x, y)
plt.title("Sine Wave")
plt.show()

# Cell 3: Markdown
## Conclusion

Final thoughts...
```

## Step 2: Render the Notebook to HTML

Use the provided script to convert all notebooks to HTML:

```bash
# From the project root
./scripts/render_jup.sh
```

This script:
- Finds all `.ipynb` files in `jup/`
- Converts them to HTML using `jupyter nbconvert`
- Saves HTML files to `app/html/local/notes/`
- Removes code prompts and input cells (only shows output)

### Manual Rendering (Alternative)

If you want to render a single notebook manually:

```bash
jupyter nbconvert --to html \
  --output-dir='app/html/local/notes' \
  --no-prompt \
  --no-input \
  jup/your-note.ipynb
```

**Options explained:**
- `--to html` - Convert to HTML format
- `--output-dir` - Where to save the HTML file
- `--no-prompt` - Hide input prompts (In[1]:, Out[1]:)
- `--no-input` - Hide code cells (only show output/markdown)

## Step 3: Add Metadata Entry

Add your note to the metadata file so it appears in the blog listing:

**File:** `app/html/local/notes/meta.csv`

```csv
seq,note,title,subtitle,created,labels
1,test,First Note,just testing,2024-02-09,test|first_one
2,your-note,Your Note Title,Brief description,2025-01-21,python|tutorial
```

**Column descriptions:**
- `seq` - Display order (lower numbers appear first)
- `note` - Notebook filename without `.ipynb` (must match HTML filename)
- `title` - Display title for the blog listing
- `subtitle` - Brief description/subtitle
- `created` - Publication date (YYYY-MM-DD format)
- `labels` - Tags separated by pipe `|` character

### Example Entry

For a notebook `jup/machine-learning-basics.ipynb`:

```csv
3,machine-learning-basics,Machine Learning Basics,Introduction to ML concepts,2025-01-21,ml|python|tutorial
```

## Step 4: Verify Your Note

1. **Start the application:**
   ```bash
   source venv/bin/activate
   export FLASK_ENV='lite'
   flask run
   ```

2. **View the blog listing:**
   - Navigate to `/blog_posts` or click "Thoughts" in the sidebar
   - Your note should appear in the list

3. **View your note:**
   - Click on the note title
   - Or navigate directly to `/blog/your-note`
   - The HTML will be rendered within the site layout

## Routes and Templates

### Blog Routes (defined in `ssk/blueprints/home.py`)

- **`/blog_posts`** - Lists all blog posts
  - Reads `meta.csv` and displays all notes
  - Template: `ssk/templates/ssk/posts.html`

- **`/blog/<note>`** - Displays a specific note
  - Renders HTML from `app/html/local/notes/<note>.html`
  - Template: `ssk/templates/local/notebook.html`
  - Includes a contact form in the sidebar

### Template Structure

**`ssk/templates/local/notebook.html`:**
- Main layout with sidebar
- Includes the rendered HTML note
- Provides a contact form for reader feedback

**`ssk/templates/ssk/posts.html`:**
- Lists all blog posts with title, subtitle, date, and labels
- Links to individual note pages

## Advanced: Customizing the Layout

### Modify the Note Template

Edit `app/html/local/notebook.html` to customize how notes are displayed:

```html
{% extends 'local/layout.html' %}

{% block main %}
    <div class="row">
        <div class="col-md-8">
            {% include toshow %}  <!-- Rendered note HTML -->
        </div>
        <div class="col-md-4">
            <!-- Sidebar content (e.g., contact form) -->
        </div>
    </div>
{% endblock %}
```

### Add Custom CSS for Notebooks

Add styles to `app/assets/local/global.css`:

```css
/* Notebook styling */
.jp-Cell {
    margin-bottom: 1rem;
}

.jp-OutputArea {
    padding: 1rem;
    background: #f8f9fa;
}
```

## Troubleshooting

### Note Not Appearing in List

1. **Check `meta.csv`** - Ensure entry exists and is properly formatted
2. **Check note name** - Must match exactly (case-sensitive)
3. **Check CSV format** - Use commas as delimiters, no extra spaces
4. **Restart app** - CSV is read on page load

### Note Shows 404 Error

1. **Check HTML file exists** - Look in `app/html/local/notes/`
2. **Check filename** - Must be `<note>.html` (not `.ipynb`)
3. **Re-run render script** - May need to regenerate HTML

### Notebook Not Converting

1. **Check Jupyter installed:**
   ```bash
   jupyter --version
   ```

2. **Install if missing:**
   ```bash
   pip install jupyter nbconvert
   ```

3. **Check for errors:**
   ```bash
   jupyter nbconvert --to html jup/your-note.ipynb
   ```

### Code Cells Showing When They Shouldn't

Make sure you're using the `--no-input` flag in the render script:
```bash
jupyter nbconvert --to html --no-input jup/*.ipynb
```

## Best Practices

### Content

- **Use descriptive titles** - Help readers understand the content
- **Add meaningful subtitles** - Provide context at a glance
- **Tag appropriately** - Use consistent labels for easy filtering
- **Include images** - Embed visualizations and diagrams
- **Test code cells** - Run all cells before rendering

### Organization

- **Use semantic filenames** - `data-analysis-2024-q1.ipynb` not `notebook1.ipynb`
- **Number by sequence** - Use `seq` in meta.csv for ordering
- **Keep notebooks focused** - One topic per notebook
- **Update dates** - Use actual publication dates in meta.csv

### Performance

- **Optimize images** - Large images slow page load
- **Limit output** - Truncate long outputs in notebooks
- **Pre-render** - Convert to HTML before deployment, not on-demand

## Workflow Summary

```bash
# 1. Create notebook
cd jup/
jupyter notebook
# ... write your content ...

# 2. Render to HTML
cd ..
./scripts/render_jup.sh

# 3. Add metadata
echo "3,my-note,My Note Title,Description,2025-01-21,tag1|tag2" >> app/html/local/notes/meta.csv

# 4. Test locally
flask run
# Navigate to http://localhost:5000/blog_posts

# 5. Commit and deploy
git add jup/my-note.ipynb app/html/local/notes/my-note.html app/html/local/notes/meta.csv
git commit -m "Add new blog post: My Note Title"
git push
```

## Alternative: Manual HTML Notes

If you don't want to use Jupyter, you can create HTML files directly:

1. **Create HTML file** in `app/html/local/notes/my-note.html`
2. **Add metadata** to `meta.csv`
3. **Access via** `/blog/my-note`

The HTML will be included in the notebook template automatically.

## Future Enhancements

Potential improvements to consider:

- **Automated rendering** - Job to convert notebooks on schedule
- **Draft/Published status** - Hide unpublished notes
- **Categories** - Group notes by category
- **RSS feed** - Generate feed from meta.csv
- **Search functionality** - Full-text search across notes
- **Comments** - Reader comments on notes

## Support

For issues or questions:
- Check logs in `log/web.log`
- Review the blueprint: `ssk/blueprints/home.py`
- Examine templates: `ssk/templates/local/notebook.html`
- GitHub Issues: https://github.com/acodingmind/soseki/issues
