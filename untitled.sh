apt update
apt upgrade 

echo "🧹 Clearing pip cache..."
pip3 cache purge || true

# Optional: Clean .git and __pycache__
echo "🧽 Removing .git and __pycache__ folders..."
rm -rf .git || true
find . -type d -name '__pycache__' -exec rm -rf {} + || true

# Update APT and install FFmpeg, Python, and pip
echo "🔁 Updating APT and installing FFmpeg, Python, pip..."
apt-get update -y
apt-get install -y ffmpeg python3 python3-pip

# Upgrade pip
echo "📦 Upgrading pip..."
pip3 install --upgrade pip

# Install individual Python packages with version pinning
echo "📦 Installing specific Python packages..."
pip3 install "lxml[html_clean]"
pip3 install --use-pep517 --no-build-isolation html-telegraph-poster
pip3 install --use-pep517 --no-build-isolation pyaes
pip3 install --use-pep517 --no-build-isolation anitopy
pip3 install --use-pep517 --no-build-isolation sgmllib3k

# Install from requirements.txt
if [ -f "requirements.txt" ]; then
  echo "📜 Installing from requirements.txt..."
  pip3 install -r requirements.txt
else
  echo "⚠️ requirements.txt not found, skipping..."
fi

echo "✅ Setup complete."
