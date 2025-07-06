# Streamlit Portal Server

A comprehensive, production-ready server solution that transforms your Streamlit deployment into a powerful portal with advanced authentication, full user management, automated app discovery, and modern UI design. Perfect for enterprise environments running multiple Streamlit applications.

## Key Features

### Advanced Authentication & Security
- **Secure user login/logout** with bcrypt password hashing
- **Role-based access control** (Admin/User roles)
- **Portal session management** with secure cookies and automatic restoration
- **Access token system** with session binding to prevent URL sharing
- **Group-based permissions** for granular access control
- **App ID security validation** to prevent unauthorized app access
- **Protected user accounts** (prevent deletion of admin/current user)

### Complete User Management
- **Full CRUD operations** - Create, Read, Update, Delete users
- **Smart user editing** with form pre-population
- **Flexible user information** (username, full name, email, role)
- **Group membership management** with comma-separated input
- **User activity tracking** with last login timestamps
- **Safety protections** against accidental admin deletion
- **Password management** with optional password updates

### Advanced Application Management
- **Auto-discovery** of running Streamlit applications
- **Full app lifecycle** - Create, edit, delete, monitor
- **Rich app metadata** (name, description, category, custom images)
- **App ID security integration** - Each app gets unique ID for security validation
- **Port scanning** for unregistered applications (8502-8600 range)
- **Real-time status monitoring** with caching for performance
- **Category-based organization** with filtering
- **Image upload support** with automatic resizing and optimization

### Smart App Discovery
- **Automated port scanning** with multithreaded performance
- **HTTP verification** to confirm Streamlit applications
- **Cache management** (1-minute TTL) for optimal performance  
- **Exclusion of registered ports** to show only new discoveries
- **Direct launch buttons** for unregistered apps
- **Scan statistics** and status reporting

### Modern UI/UX Design
- **Professional mature theme** with clean, enterprise-grade design
- **Custom Streamlit theming** via `.streamlit/config.toml`
- **Status indicators** (🟢 Running, 🔴 Offline, 🟢 Active, 🔴 Inactive)

### Granular Permission System
- **Group-based access control** with flexible group assignment
- **Per-application permissions** configuration
- **🌐 Public Access** - Apps accessible to all users without group restrictions
- **Admin oversight capabilities** with full system access
- **Automatic permission inheritance** for new users
- **Visual permission management** interface

### Performance Optimizations
- **Intelligent caching** with `@st.cache_data` decorators
- **Optimized port checking** (30-second TTL for status, 60-second TTL for scans)
- **Multithreaded port scanning** (max 50 workers) with timeout handling
- **Selective port monitoring** (only check accessible apps per user)
- **Lazy loading** for large datasets and images

## Quick Start

### Prerequisites
- **Python 3.8+**
- **Required packages** (automatically installed via requirements.txt)
- **Network Access**: For multi-user access, the server must be on the same network as the users

### Installation

**Recommended: Using UV (Fast & Modern)**

1. **Install UV** (if not already installed):
   ```bash
   # On Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/guinacio/streamlit-portal-server.git
   cd streamlit-portal-server
   ```

3. **Install dependencies with UV**:
   ```bash
   uv sync
   ```

4. **Run the portal**:
   ```bash
   uv run streamlit run app.py
   ```

5. **Access the portal**:
   - **Local access**: `http://localhost:8501`
   - **Network access**: `http://[SERVER-IP]:8501` (replace [SERVER-IP] with your server's IP address)

**Alternative: Using pip**

If you prefer using pip or don't want to install UV:

```bash
# After cloning the repository
pip install -r requirements.txt
streamlit run app.py
```

> **💡 Why UV?** UV is significantly faster than pip, has better dependency resolution, and provides more reliable virtual environment management. It's the modern choice for Python package management.

### Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Security Notice**: Change the default admin password immediately after first login!

![Login Screen](images/login-screen.png)

## Comprehensive Usage Guide

### For Administrators

#### 1. **Advanced Application Management**
Navigate to **Admin Panel → Manage Apps**

![App Management](images/app-management.png)

**Adding/Editing Applications:**
- Select "Create New App" or choose existing app from dropdown
- Configure port number, name, description, and category
- Upload custom images (PNG, JPG, JPEG) with automatic optimization
- Form pre-populates when editing existing apps
- Save changes with real-time validation

**Managing Existing Apps:**
- View all apps with status indicators (🟢 Running, 🔴 Offline)
- **App ID Display**: Each app shows its unique ID for security library integration
- Edit any application by selecting it from the dropdown
- Delete applications with confirmation (removes from permissions too)
- Monitor app categories and descriptions
- Copy App IDs for use in the `app_security.py` library

**Automated App Discovery:**
- Click "🔍 Scan for Unregistered Apps" to find running apps on ports 8502-8600
- Results are cached for 1 minute for performance
- Automatically excludes already registered ports
- Direct "Open" buttons to launch unregistered apps
- Clear cache button for fresh scans

#### 2. **Complete User Management**
Navigate to **Admin Panel → Manage Users**

![User Management](images/user-management.png)

**Creating/Editing Users:**
- Select "Create New User" or choose existing user from dropdown
- Configure username (locked when editing), full name, email
- Set role (admin/user) and assign to groups (comma-separated)
- Password management: optional updates (leave empty to keep current)
- Form pre-populates all fields when editing

**User Overview:**
- Visual user cards showing username, full name, and email
- Role and group membership display
- Activity status (🟢 Active, 🔴 Inactive)
- Last login timestamps with formatted dates
- Individual delete buttons with safety protections

**Safety Features:**
- Cannot delete admin user or currently logged-in user
- Protected users show 🔒 icon instead of delete button
- Automatic cleanup removes users from all groups when deleted
- Transaction safety prevents data corruption

#### 3. **Permission Management**
Navigate to **Admin Panel → Groups & Permissions**

![Permission Management](images/permissions.png)

**Setting App Permissions:**
- Select application from dropdown
- Choose which user groups can access the app
- **🌐 Public (All Users)**: Select this option to make an app accessible to ALL users, regardless of group membership
- Multi-select interface with current permissions pre-selected
- Save changes with immediate effect
- Visual feedback for successful updates

**Access Levels:**
- **🌐 Public Access**: App is accessible to all users (great for common tools, dashboards everyone needs)
- **🔒 Group Access**: App is only accessible to users in specific groups  
- **⚠️ No Access**: App is not accessible to any users

#### 4. **System Monitoring**
- **Dashboard Statistics**: Total apps, running apps, total users (admin view)
- **Port Status Caching**: 30-second cache for app status checks
- **Performance Metrics**: Scan timing and success rates
- **User Activity**: Login timestamps and activity monitoring

### For Users

![User Dashboard](images/user-dashboard.png)

#### 1. **Accessing Applications**
- **Dashboard View**: See all applications you have permission to access
- **Smart Filtering**: Search by name, description, or category
- **Category Filtering**: Filter apps by category (General, Analytics, ML/AI, etc.)
- **Status Indicators**: Know which apps are running (🟢) or offline (🔴)

#### 2. **Launching Applications**
- Click **"🚀 Launch App"** on running applications
- Apps open in new browser tabs with secure access tokens
- Portal page automatically refreshes to renew tokens after launching
- Only applications you have group permissions for are displayed
- Secure access through FastAPI proxy server (port 8000)

#### 3. **User Experience Features**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Status refreshes automatically
- **Performance Optimized**: Fast loading with intelligent caching
- **Modern Interface**: Professional design with smooth interactions

## Architecture

### System Overview
The Streamlit Portal uses a multi-component architecture that ensures secure, scalable application management:

- **Portal Server** (Port 8501): Main application for user management and authentication
- **Proxy Server** (Port 8000): Secure app access with session validation
- **Database Layer**: SQLite database for user data and session management
- **Streamlit Applications** (Port 8502+): Individual apps with integrated security

### Application Flow
The following sequence diagram illustrates the complete user journey from login to secure app access:

![Sequence Diagram](images/sequence_diagram.svg)

### Key Security Checkpoints
1. **Authentication**: User login with bcrypt password validation
2. **Session Management**: Secure cookie-based session tracking
3. **Permission Validation**: Group-based app access control
4. **Token Generation**: Single-use access tokens with session binding
5. **Proxy Validation**: Multi-layer security verification
6. **App Protection**: Individual app security with ID validation

## Network Configuration

### Multi-User Network Setup

For teams and enterprise environments where multiple users need access:

**Network Requirements:**
- **Same Network**: The server hosting the portal must be on the same local network (LAN) as the users
- **Port Access**: Ensure ports 8501 (portal) and 8000 (proxy) are accessible across the network
- **Firewall**: Configure firewall rules to allow traffic on these ports if needed

**Access Methods:**
- **Local Development**: `http://localhost:8501` (single machine)
- **Team Access**: `http://192.168.1.100:8501` (replace with your server's IP)
- **Corporate Network**: `http://10.0.1.50:8501` (corporate IP range)

**Finding Your Server IP:**
```bash
# On Windows
ipconfig

# On macOS/Linux  
ifconfig
# or
ip addr show
```

**Example Network Setup:**
```
Corporate Network (10.0.1.0/24)
├── Server: 10.0.1.50 (Running portal on port 8501)
├── User 1: 10.0.1.101 (Accesses http://10.0.1.50:8501)
├── User 2: 10.0.1.102 (Accesses http://10.0.1.50:8501)
└── User 3: 10.0.1.103 (Accesses http://10.0.1.50:8501)
```

**Security Considerations:**
- The portal automatically uses the server's IP for all internal communications
- All Streamlit apps must run on the same server for security and network access
- Apps are accessed through the secure proxy server (port 8000) with session validation

## Configuration & Customization

### File Structure
```
streamlit-portal-server/
├── app.py                    # Main Streamlit portal application
├── database.py              # Database operations and models  
├── utils.py                 # Utility functions and helpers
├── app_security.py          # Security library for protecting individual apps
├── proxy_server.py          # FastAPI proxy server for secure app access
├── run_demo.py              # Demo startup script with sample apps
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Modern Python project configuration
├── .cursorrules            # AI development guidelines
├── .streamlit/
│   └── config.toml         # Streamlit theme configuration
├── demo_apps/              # Sample applications with security integration
│   ├── demo_app_1.py       # Analytics Dashboard (App ID 1)
│   └── demo_app_2.py       # ML Model Playground (App ID 2)
├── app_images/             # Uploaded app images (auto-created)
├── portal.db              # SQLite database (auto-created)
└── README.md              # This documentation
```

### Database Configuration
- **SQLite database** (`portal.db`) created automatically on first run
- **Automatic migrations** handle schema updates
- **Foreign key constraints** ensure data integrity
- **Indexed queries** for optimal performance

### Theme Customization
The portal uses a custom theme defined in `.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#888888"           # Light gray for button text/interactions
backgroundColor = "#ffffff"        # Clean white background
secondaryBackgroundColor = "#f8f9fa"  # Subtle gray for cards
textColor = "#2c3e50"              # Professional dark gray
linkColor = "#2980b9"              # Theme blue for links
```

### Port Range Configuration
Modify the scanning range in `display_unregistered_ports()`:
```python
# Scan ports 8502-8600 (default)
unregistered_ports = scan_unregistered_ports_cached(8502, 8600, registered_ports)
```

### Categories Customization
Add new categories in `manage_apps_tab()`:
```python
category = st.selectbox("Category", 
    ["General", "Analytics", "ML/AI", "Dashboard", "Tools", "Games", "Your-Category"])
```

## Development & Testing

### Running Multiple Test Apps
Test the portal with multiple Streamlit applications:

1. **Create test applications**:
   ```bash
   mkdir test_apps && cd test_apps
   mkdir app1 app2 app3
   ```

2. **Create simple test apps**:
   ```python
   # test_apps/app1/main.py
   import streamlit as st
   st.title("Analytics Dashboard")
   st.write("Sample analytics application")
   st.bar_chart({"data": [1, 2, 3, 4, 5]})
   ```

3. **Run on different ports**:
   ```bash
   # Terminal 1
   cd test_apps/app1 && streamlit run main.py --server.port 8502
   
   # Terminal 2  
   cd test_apps/app2 && streamlit run main.py --server.port 8503
   
   # Terminal 3
   cd test_apps/app3 && streamlit run main.py --server.port 8504
   ```

4. **Configure in portal**:
   - Login as admin
   - Use "Scan for Unregistered Apps" to auto-discover
   - Register apps with proper names, descriptions, and categories
   - Create user groups and set permissions
   - Test access with different user accounts

## Security Features

### Enterprise-Grade Security
The Streamlit Portal implements multiple layers of security to protect against unauthorized access and ensure safe application deployment in enterprise environments.

### Multi-Layer Authentication
- **Session-Based Security**: Advanced session management with secure token validation
- **Anti-Sharing Protection**: URLs cannot be shared between users or browsers
- **Automatic Token Expiration**: Access tokens expire automatically and are single-use only
- **Session Binding**: All access is cryptographically tied to authenticated portal sessions
- **Logout Protection**: When users log out, all their active sessions become invalid immediately

### Secure Access Control
- **Portal Session Validation**: Database-backed session verification prevents unauthorized access
- **Token-to-Session Binding**: Access tokens are permanently linked to the portal session that created them
- **Cross-Platform Security**: Works reliably across different browsers and devices
- **Non-Repudiation**: Clear audit trail of who accessed what and when

### Application Protection with App ID Security
Each Streamlit application can be secured using the included security library with mandatory app ID validation:

```python
from app_security import require_portal_access

# At the top of your Streamlit app (after page config)
require_portal_access(app_id=123)  # MUST match your app's ID from the portal database
```

**How App ID Security Works:**

1. **Portal Database Registration**: Each app registered in the portal gets a unique numeric ID
2. **Security Library Integration**: Apps use `app_security.py` with their specific app ID
3. **ID Matching Validation**: The portal validates that the requested app ID matches the authenticated session token
4. **Access Denial**: If app IDs don't match, access is immediately denied, if tokens don't match or are expired, denied

**Setting Up App Security:**

1. **Register your app** in the Portal Admin Panel → Manage Apps
2. **Note the App ID** displayed in the management interface (see admin guide below)
3. **Add security to your Streamlit app:**
   ```python
   import streamlit as st
   from app_security import require_portal_access
   
   # Page config first
   st.set_page_config(page_title="My App", page_icon="📊")
   
   # Security check with your app's ID - CRITICAL: Use the correct ID!
   require_portal_access(app_id=123)  # Replace 123 with your actual app ID
   
   # Your app code continues here
   st.title("My Secure Application")
   ```

4. **Deploy your app** on the port specified in the portal registration

**Security Benefits:**
- **Prevents unauthorized access** even with valid portal sessions
- **App-specific access control** - users can only access apps they have permissions for
- **ID spoofing protection** - apps cannot impersonate other applications
- **Database-backed validation** - all access is verified against the portal database

### Security Best Practices

#### Authentication Security
- **bcrypt password hashing** with salt for secure storage
- **Session management** prevents unauthorized access
- **Role-based permissions** limit access based on user roles
- **Input validation** on all user inputs to prevent injection attacks
- **Secure session cookies**

#### Database Security  
- **Parameterized queries** prevent SQL injection
- **Foreign key constraints** maintain data integrity
- **Transaction safety** ensures atomic operations
- **Connection management** with proper cleanup
- **Session state protection** with database validation

#### Access Security
- **Group-based permissions** for granular access control
- **Public/private app designation** with clear security boundaries
- **Admin privilege separation** with protected account controls
- **Automatic session cleanup** removes expired sessions
- **Single-use tokens** prevent replay attacks

#### Network Security
- **Port scanning protection** with controlled discovery ranges
- **HTTP verification** ensures only legitimate applications are discovered
- **Cross-origin protection** prevents unauthorized embedding
- **Secure proxy architecture** with cookie-based session management

#### File Security
- **Image upload validation** (type, size restrictions)
- **Path sanitization** prevents directory traversal
- **Secure file storage** in designated directories
- **File type restrictions** with automatic processing

## Troubleshooting

### Common Issues & Solutions

1. **"No apps found" / Empty Dashboard**
   - Verify Streamlit apps are running on expected ports
   - Check user has group permissions for apps
   - Confirm apps are registered in admin panel
   - Use "Scan for Unregistered Apps" to auto-discover

2. **Authentication Problems**
   - Verify username/password spelling and case sensitivity
   - Check user account is active (not disabled)
   - Try with default admin credentials
   - Check database permissions and file access

3. **Port Scanning Issues**
   - Ensure ports 8502-8600 are not blocked by firewall
   - Check if services are actually Streamlit apps (HTTP verification)
   - Clear scan cache if results seem stale
   - Verify multithreading isn't blocked by system limits

4. **Image Upload Problems**
   - Check `app_images/` directory is writable
   - Verify file format (PNG, JPG, JPEG only)
   - Ensure PIL/Pillow is correctly installed
   - Check file size limits (images are auto-resized)

5. **Database Errors**
   - Ensure directory is writable for SQLite file creation
   - Check `portal.db` file permissions
   - Verify no conflicting database connections
   - Restart application if database is locked

6. **Theme/UI Issues**
   - Verify `.streamlit/config.toml` file is present
   - Clear browser cache to refresh CSS
   - Check for JavaScript console errors
   - Ensure Streamlit version supports theme features

7. **Network Access Issues**
   - Verify server and users are on the same network (LAN)
   - Check firewall settings for ports 8501 and 8000
   - Confirm server IP address is accessible from user machines
   - Test with `ping [SERVER-IP]` from user machines
   - Ensure no network restrictions block HTTP traffic

## Contributing

We welcome contributions! Here's how to get involved:

### Reporting Issues
- Use GitHub Issues with detailed reproduction steps
- Include system information (OS, Python version, Streamlit version)
- Provide logs and error messages when applicable

### Suggesting Features
- Check existing issues for similar requests
- Provide detailed use cases and expected behavior
- Consider backwards compatibility and security implications

### Code Contributions
- Write tests for new features
- Update documentation for changes
- Use consistent code style and commenting

## License

This project is open source and available under the **MIT License**.

## Acknowledgments

Built with these amazing technologies:

- **[Streamlit](https://streamlit.io/)** - The powerful Python web app framework
- **[SQLite](https://sqlite.org/)** - Lightweight, reliable database engine  
- **[bcrypt](https://github.com/pyca/bcrypt)** - Secure password hashing
- **[Pillow](https://python-pillow.org/)** - Python image processing library
- **[pandas](https://pandas.pydata.org/)** - Data manipulation and analysis

