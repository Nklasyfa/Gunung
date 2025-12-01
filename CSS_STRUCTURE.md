# CSS Structure Documentation

## Folder Organization

```
static/css/
├── base.css                 # Global styles (shared)
├── edit_profile.css        # Legacy (old structure)
├── home.css                # Legacy (old structure)
├── login.css               # Legacy (old structure)
├── payment.css             # Legacy (old structure)
│
├── user/                   # User-facing pages
│   ├── dashboard.css       # User dashboard page
│   ├── bantuan.css         # User help/support page
│   ├── profile.css         # User profile & account pages
│   └── pemesanan.css       # User booking/order page
│
└── admin/                  # Admin pages
    ├── dashboard.css       # Admin dashboard
    └── bantuan.css         # Admin help page
```

## CSS Files Description

### Global Styles
- **base.css**: Contains global styling, variables, dark mode CSS, sidebar styles, base components

### User Pages (`static/css/user/`)

#### dashboard.css
- User dashboard/home page styling
- Mountain cards with hover effects
- Grid layout for responsive design
- Gradient buttons and controls
- Dark mode support
- Mobile responsive

#### bantuan.css
- Help/support page styling
- Help sections with left border accent
- FAQ items with hover effects
- Contact buttons (WhatsApp, Email, Chat)
- Horizontal dividers with gradient
- Smooth animations

#### profile.css
- Profile and account pages
- Form sections and inputs
- Profile header with gradient
- Avatar/photo upload section
- Info display rows
- Form validation styles

#### pemesanan.css
- Booking/order form page
- Booking cards grid
- Price breakdown section
- Form inputs and validation
- Status badges (pending, confirmed, cancelled)
- Terms & conditions checkbox

### Admin Pages (`static/css/admin/`)

#### dashboard.css
- Admin dashboard professional styling
- Stats grid cards
- Data tables with hover effects
- Action buttons (edit, delete, view)
- Modal dialogs
- Professional color scheme

#### bantuan.css
- Admin help page styling
- Similar structure to user bantuan but with professional blue colors
- Admin-specific contact information
- FAQ sections for technical support
- Professional styling with accent colors

## Color Scheme

### User Pages (Purple Gradient)
- Primary Gradient: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Primary Color: #667eea
- Secondary Color: #764ba2
- Accent Color: #f5576c
- Success: #27ae60
- Warning: #f39c12
- Danger: #e74c3c

### Admin Pages (Blue Theme)
- Primary Color: #2c3e50 (dark blue-gray)
- Accent Color: #3498db (bright blue)
- Success: #27ae60 (green)
- Warning: #f39c12 (orange)
- Danger: #e74c3c (red)

## Typography

- Font Family: Montserrat (inherited from base)
- Headings: Font weight 700-800
- Body text: Font weight 400-600
- Font sizes: Responsive scaling

## Responsive Breakpoints

- **Desktop**: 1200px and above
- **Tablet**: 768px - 1199px
- **Mobile**: 480px - 767px
- **Small Mobile**: Below 480px

## Dark Mode Implementation

All CSS files include dark mode support using:
```css
body.dark-mode .selector {
    /* Dark mode styles */
}
```

Dark mode persists via localStorage (managed in base.html JavaScript)

## Transitions & Animations

- Default transition: `all 0.3s cubic-bezier(0.4, 0, 0.2, 1)`
- Hover transforms: `translateY(-8px)` for cards, `translateY(-2px)` for buttons
- Fade-in animations for page loads
- Slide animations for modals

## Shadows

- Card Shadow: `0 10px 30px rgba(102, 126, 234, 0.15)`
- Hover Shadow (user): `0 20px 40px rgba(102, 126, 234, 0.25)`
- Hover Shadow (admin): `0 15px 40px rgba(52, 152, 219, 0.2)`

## How to Use

### Import CSS in Templates

Add to the `{% block extra_css %}` section:

```html
{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/user/dashboard.css') }}">
{% endblock %}
```

### Create New Page Styles

1. Create new file in `static/css/user/` or `static/css/admin/`
2. Use root variables for consistency
3. Include responsive media queries
4. Add dark mode support
5. Import in template using `{% block extra_css %}`

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- IE11: Limited support (no CSS Grid in some sections)

## Performance Notes

- CSS files are separate to enable caching per page
- Only required CSS loads for each page
- Minimal use of complex selectors
- Hardware-accelerated animations where possible
