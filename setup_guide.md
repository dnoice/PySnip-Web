# PySnip Explorer - Setup Guide

This guide will help you set up the PySnip Explorer web interface on your Termux PRoot-Distro Ubuntu environment.

## Prerequisites

Ensure you have the following set up:
- Termux with PRoot-Distro Ubuntu installed
- Python 3.8+ in your Ubuntu environment
- A virtual Python environment (recommended)
- Storage permissions for Termux

## Installation Steps

### 1. Create Project Directory

First, create a directory for the PySnip Explorer and navigate to it:

```bash
mkdir -p ~/pysnip-explorer
cd ~/pysnip-explorer
```

### 2. Set Up Virtual Environment (if not already done)

```bash
# Install virtualenv if not installed
apt-get update
apt-get install -y python3-venv

# Create virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

### 3. Install Required Dependencies

Create a requirements.txt file with the following contents:

```
Flask==2.3.2
Werkzeug==2.3.6
Jinja2==3.1.2
itsdangerous==2.1.2
click==8.1.3
MarkupSafe==2.1.2
python-dotenv==1.0.0
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

### 4. Create Project Structure

Create the necessary directories for the project:

```bash
mkdir -p static/css static/js static/images
mkdir -p templates
mkdir -p utils
```

### 5. Copy Application Files

Copy all the provided Python, HTML, CSS, and JavaScript files to their respective directories. Make sure the file structure matches the following:

```
pysnip-explorer/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── static/             # Static assets
│   ├── css/main.css    # Styling
│   ├── js/script.js    # UI interactivity 
│   └── images/         # Icons and images
├── templates/          # HTML templates
│   ├── index.html      # Home/catalog page
│   ├── category.html   # Category view
│   ├── tool.html       # Individual tool view
│   ├── 404.html        # Error page
│   └── base.html       # Base template
└── utils/              # Utility modules
    ├── scanner.py      # Directory scanner
    ├── executor.py     # Script execution handler
    └── doc_parser.py   # Documentation extractor
```

### 6. Configure the Application

Edit the `config.py` file to set the path to your PySnip root directory:

```python
# Change this to match your PySnip root directory path
PYSNIP_ROOT = os.environ.get('PYSNIP_ROOT', os.path.join(os.path.expanduser('~'), 'pysnip'))
```

### 7. Run the Application

Now you can run the Flask application:

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

Or simply:

```bash
python app.py
```

### 8. Access the Web Interface

The web interface should now be accessible at:

- Local access: http://localhost:5000
- From other devices on the same network: http://YOUR_IP_ADDRESS:5000

To find your IP address, you can use:

```bash
ip addr show
```

Look for the `inet` address on your WiFi interface (usually `wlan0`).

## Common Issues and Solutions

### Issue: Cannot connect to the web interface

**Solution**:
- Make sure you're running the Flask app with `--host=0.0.0.0` to allow external connections
- Check if any firewall is blocking port 5000
- Verify your IP address is correct

### Issue: "No such file or directory" when scanning PySnip

**Solution**:
- Check if the `PYSNIP_ROOT` path in `config.py` is correct
- Make sure your PySnip directory exists and is accessible
- Try using an absolute path instead of a relative path

### Issue: Tool execution fails

**Solution**:
- Verify that you have the necessary permissions to execute the tool
- Check if the tool has any dependencies that are not installed
- Look at the error message in the web interface for more details

### Issue: Web interface is slow or unresponsive

**Solution**:
- Try reducing the `NUM_POINTS` constant in the graph plotter script
- Increase the value of `MAX_EXECUTION_TIME` in `config.py` for complex tools
- Consider running the Flask app with Gunicorn for better performance

## Customization Options

### Change Theme Colors

Edit the `static/css/main.css` file to modify the color scheme. Look for the `:root` section at the top:

```css
:root {
  /* Core Colors - Dark Theme (Default) */
  --bg-primary: #121212;
  --bg-secondary: #1e1e1e;
  /* ...more variables... */
}
```

### Add or Modify Category Icons

Edit the `get_category_icon` function in `config.py` to change the icons for categories:

```python
def get_category_icon(category_name):
    icons = {
        'automation': 'robot',
        'creative': 'paint-brush',
        # Add or modify category icons here
    }
    return icons.get(category_name, 'puzzle-piece')
```

### Customize Homepage Sections

Edit the `templates/index.html` file to add, remove, or modify sections on the homepage.

## Starting the Application Automatically

To have the PySnip Explorer start automatically when you launch your Ubuntu environment, add these lines to your `~/.bashrc` file:

```bash
# Start PySnip Explorer
if [ -d ~/pysnip-explorer ]; then
    cd ~/pysnip-explorer
    if [ -d venv ]; then
        source venv/bin/activate
        echo "Starting PySnip Explorer..."
        python app.py &
        echo "PySnip Explorer running at http://localhost:5000"
    fi
fi
```

## Enhancing the Interface

### Add Category Images

Add thumbnail images for each category in the `static/images` directory with the same name as the category (e.g., `automation.png`, `creative.png`).

### Add Tool Screenshots

Create a `static/images/tools` directory and add screenshots of your tools to display in the tool detail pages. Name the screenshots after the tool directory (e.g., `graph_plotter.png`).

## Updates and Maintenance

To update the PySnip Explorer in the future:

1. Backup your customized files
2. Pull or download the new version
3. Merge your customizations with the new version
4. Restart the application

## Conclusion

You now have a fully functional web interface for browsing and executing your PySnip collection! Explore the various categories, run tools directly from the browser, and enjoy the enhanced experience.

If you encounter any issues or have questions, feel free to reach out for assistance.
