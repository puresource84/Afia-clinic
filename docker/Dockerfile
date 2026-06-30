FROM odoo:18

USER root

# Install any extra Python dependencies if needed
RUN pip install --no-cache-dir --break-system-packages phonenumbers 2>/dev/null || true

# Copy custom odoo config
COPY odoo.conf /etc/odoo/odoo.conf

USER odoo
