#!/bin/bash

# Script to download the Bible database from HelloAO
# This database contains all English Bible translations used by the SQLite Bible client

set -e  # Exit on error

BIBLE_DB_URL="https://bible.helloao.org/bible.eng.db"
BIBLE_DB_FILE="bible.eng.db"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIBLE_DB_PATH="${SCRIPT_DIR}/${BIBLE_DB_FILE}"

echo "======================================"
echo "Bible Database Download Script"
echo "======================================"
echo ""

# Check if database already exists
if [ -f "$BIBLE_DB_PATH" ]; then
    echo "⚠️  Bible database already exists at: ${BIBLE_DB_PATH}"
    echo ""
    read -p "Do you want to re-download it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Download cancelled."
        exit 0
    fi
    echo "Removing existing database..."
    rm "$BIBLE_DB_PATH"
fi

echo "Downloading Bible database from: ${BIBLE_DB_URL}"
echo "Destination: ${BIBLE_DB_PATH}"
echo ""

# Download the database using curl with progress bar
if command -v curl &> /dev/null; then
    curl -L --progress-bar -o "$BIBLE_DB_PATH" "$BIBLE_DB_URL"
elif command -v wget &> /dev/null; then
    wget --show-progress -O "$BIBLE_DB_PATH" "$BIBLE_DB_URL"
else
    echo "❌ Error: Neither curl nor wget is available. Please install one of them."
    exit 1
fi

# Verify the download
if [ -f "$BIBLE_DB_PATH" ]; then
    FILE_SIZE=$(du -h "$BIBLE_DB_PATH" | cut -f1)
    echo ""
    echo "✅ Download complete!"
    echo "   File: ${BIBLE_DB_FILE}"
    echo "   Size: ${FILE_SIZE}"
    echo ""

    # Verify it's a valid SQLite database
    if command -v sqlite3 &> /dev/null; then
        echo "Verifying database integrity..."
        if sqlite3 "$BIBLE_DB_PATH" "SELECT COUNT(*) FROM Translation;" > /dev/null 2>&1; then
            TRANSLATION_COUNT=$(sqlite3 "$BIBLE_DB_PATH" "SELECT COUNT(*) FROM Translation;")
            echo "✅ Database is valid and contains ${TRANSLATION_COUNT} translations."
        else
            echo "⚠️  Warning: Database file may be corrupted."
        fi
    fi

    echo ""
    echo "You can now use the SQLite Bible client!"
    echo "Make sure BIBLE_CLIENT_TYPE=sqlite is set in your .env file."
else
    echo "❌ Download failed!"
    exit 1
fi
