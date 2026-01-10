# Conduit: Local Media Server

**Conduit** is a sleek, self-hosted media server that organizes your local video files into a beautiful, Netflix-style library. 

It is designed to be lightweight and simple: point it at your media folders, and it automatically fetches posters, metadata, and descriptions using the TMDB API. It features a modern, responsive dashboard with a premium dark/light mode and simple settings management.

![Dashboard Preview](Screenshots/Dashboard.png)

---

## 🚀 Key Features

*   **Smart Library**: Automatically scans your folders (`downloads` or custom paths) to discover movies and TV shows.
*   **Rich Metadata**: Uses `guessit` and `tmdbsimple` to fetch Posters, Plot Summaries, Ratings, and Runtime.
*   **Modern Dashboard**: A clean, responsive interface with **Dark Mode** support and "Hover Reveal" cards.
*   **Direct Play**: Stream standard formats (MP4) directly in the browser.
*   **Universal Playback (VLC)**: 
    *   **Transcoding**: Automatically converts unsupported formats (MKV, AVI) on-the-fly using VLC.
    *   **External Player**: One-click "Open in VLC" allows you to stream to your favorite desktop player.
*   **Settings Manager**:
    *   **Folder Picker**: Browse and add watch folders securely from the UI.
    *   **Wi-Fi Manager**: Scan and connect to networks (macOS only).

![Settings Preview](Screenshots/Settings.png)

---

## 🛠 Prerequisites

*   **Python 3.9+**
*   **VLC Media Player**: Required for transcoding and external playback support.
*   **TMDB API Key**: Free from [The Movie Database](https://www.themoviedb.org/documentation/api).
*   **OS**: macOS (optimized) or Linux/Windows.

---

## 🔧 Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yowunpansilu/Conduit.git
    cd Conduit
    ```

2.  **Create Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration**
    Create a `.env` file in the root directory:
    ```env
    # Required
    SECRET_KEY=your_random_secret_string
    TMDB_API_KEY=your_tmdb_api_key

    # Optional
    DOWNLOAD_DIR=downloads
    ```

5.  **Run the Server**
    ```bash
    python app.py
    ```
    Access the dashboard at `http://localhost:5001`.

---

## 📱 Usage

1.  **Add Media**: Drop files into `downloads/` or use **Settings > Browse** to add folders.
2.  **Scan Library**: Click **Scan Library** on the Dashboard.
3.  **Watch**: Click any poster. If it doesn't play directly, use the **Transcode** or **Open in VLC** options.

---

## 📄 License

This project is licensed under the MIT License.
