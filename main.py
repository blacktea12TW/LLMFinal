import argparse
import os
from dotenv import load_dotenv
from agent import LocalAIAgent


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="本地端 AI 代理：搜尋歌手從出道至今的所有歌曲資料。"
    )
    parser.add_argument(
        "artist",
        nargs="?",
        help="要搜尋的歌手名稱，例如：周杰倫、Taylor Swift。",
    )
    args = parser.parse_args()

    if args.artist:
        artist_name = args.artist.strip()
    else:
        artist_name = input("請輸入歌手名稱：").strip()

    if not artist_name:
        print("未輸入歌手名稱，程式結束。")
        return

    agent = LocalAIAgent()
    print(f"正在搜尋：{artist_name}，請稍候...\n")

    result_text = agent.search_artist_songs(artist_name)
    print(result_text)


if __name__ == "__main__":
    main()
