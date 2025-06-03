# Subnet 90 Website

This is the landing page for subnet90.com - the official website for DegenBrain Subnet 90 on Bittensor.

## Important: Images Setup

The website expects an Open Graph image at:
```
website/images/subnet-90-og.png
```

Make sure to place your `subnet-90-og.png` file in the `images/` directory before deploying.

### Image Requirements:
- **Recommended size**: 1200x630 pixels (for optimal social sharing)
- **Format**: PNG
- **File name**: `subnet-90-og.png`

## Quick Deploy

1. Copy this `website` directory to its own repository
2. Update the GitHub links in `index.html` to point to your actual repo
3. Deploy to your preferred hosting:
   - **GitHub Pages**: Push to `gh-pages` branch
   - **Netlify**: Drop folder or connect GitHub
   - **Vercel**: Import GitHub repo
   - **Static hosting**: Upload files to any web server

## Customization

### Update Links
Search and replace these placeholders in `index.html`:
- `https://github.com/yourusername/bittensor-subnet-90-brain` → Your GitHub repo
- `https://taostats.io/subnets/netuid-90/` → Verify this is the correct Taostats link
- Discord/Twitter/Telegram links → Your community links

### Colors
Edit CSS variables in `styles.css`:
```css
:root {
    --primary: #6366f1;     /* Main brand color */
    --secondary: #10b981;   /* Accent color */
    --dark: #111827;        /* Text color */
}
```

### Content
- Hero section: Main messaging
- Process flow: How the subnet works
- Token section: $BRAIN token information
- Quick start code examples

## Structure

```
website/
├── index.html      # Main HTML file
├── styles.css      # All styling
└── README.md       # This file
```

## Features

- ✅ Fully responsive design
- ✅ Clean, modern UI
- ✅ Fast loading (minimal JS)
- ✅ SEO optimized with Open Graph & Twitter Cards
- ✅ Brain emoji (🧠) favicon
- ✅ Accessible
- ✅ Print-friendly code blocks

## Preview

To preview locally:
```bash
# Python
python -m http.server 8000

# Node.js
npx http-server

# Or just open index.html in browser
```

## License

Same as parent project - use freely for Subnet 90 promotion.