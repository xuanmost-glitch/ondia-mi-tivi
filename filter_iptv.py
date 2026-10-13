import concurrent.futures
import time
import requests

# 1. Danh sách các nguồn tổng hợp (Việt Nam + Quốc tế)
SOURCES = [
    "https://iptv-org.github.io/iptv/countries/vn.m3u",       # Kênh Việt Nam
    "https://iptv-org.github.io/iptv/categories/news.m3u",     # Tin tức quốc tế
    "https://iptv-org.github.io/iptv/categories/sports.m3u",   # Thể thao
]

# Giả lập trình duyệt chuẩn để gửi yêu cầu nhẹ nhàng
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def check_single_stream(channel):
    """Gửi HEAD request nhẹ để kiểm tra xem link có phản hồi 200 hay không."""
    url = channel["url"]
    try:
        # Nghỉ nhẹ 0.05 giây để tránh gửi dồn dập vào cùng một server
        time.sleep(0.05)
        response = requests.head(url, headers=HEADERS, timeout=4, allow_redirects=True)
        if response.status_code == 200:
            return channel
    except Exception:
        pass
    return None

def fetch_and_parse_sources():
    """Tải và bóc tách từng dòng thông tin #EXTINF cùng link URL."""
    channels = []
    print("📥 Đang tải các nguồn phát m3u...")
    for src in SOURCES:
        try:
            res = requests.get(src, headers=HEADERS, timeout=10)
            lines = res.text.splitlines()
            info = None
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF:"):
                    info = line
                elif line.startswith("http") and info:
                    channels.append({"info": info, "url": line})
                    info = None
        except Exception as e:
            print(f"⚠️ Không tải được nguồn {src}: {e}")
    return channels

def main():
    channels = fetch_and_parse_sources()
    print(f"🔍 Đã tìm thấy {len(channels)} kênh. Bắt đầu quét kiểm tra link sống...")

    # Giới hạn 20 luồng (worker) để không làm nghẽn mạng hay bị đánh dấu spam
    active_channels = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(check_single_stream, channels)
        for res in results:
            if res:
                active_channels.append(res)

    # Xuất ra file m3u hoàn chỉnh
    output_file = "playlist_clean.m3u"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in active_channels:
            f.write(f"{ch['info']}\n{ch['url']}\n")

    print(f"✅ Hoàn tất! Đã lưu {len(active_channels)} kênh hoạt động tốt vào file '{output_file}'.")

if __name__ == "__main__":
    main()