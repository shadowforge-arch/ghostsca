import aiohttp
import asyncio
import pandas as pd
import sqlite3
import argparse
import time
import random
import re
import hashlib
import json
from datetime import datetime

DB_NAME = 'shadow_vault.db'
UAS = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/91.0'
]

class AlchemyStub:
    def __init__(self):
        self.status = "connected"
    
    def get_chain_whispers(self, sub):
        if sub in ['ethereum', 'ethtrader', 'defi']:
            return {'gas': random.randint(20, 150), 'vol': 'high' if random.random() > 0.5 else 'low'}
        return {'gas': 0, 'vol': 'n/a'}

async def fetch_sub(session, sub, depth, ghost_factor, sem):
    url = f"https://www.reddit.com/r/{sub}/top.json?limit={depth}&t=day"
    ua = random.choice(UAS)
    headers = {'User-Agent': ua}
    
    async with sem:
        if ghost_factor > 0:
            sleep_time = random.uniform(0.5, 1.5) * ghost_factor
            await asyncio.sleep(sleep_time)
            
        print(f"[*] Snagging r/{sub} with UA-hash: {hashlib.md5(ua.encode()).hexdigest()[:6]}...")
        
        retries = 3
        for i in range(retries):
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = []
                        children = data.get('data', {}).get('children', [])
                        for child in children:
                            p = child['data']
                            posts.append({
                                'sub': sub,
                                'title': p.get('title'),
                                'score': p.get('score'),
                                'ts': p.get('created_utc'),
                                'url': p.get('url')
                            })
                        return posts
                    elif response.status == 429:
                        wait = 2 ** (i + 1)
                        print(f"[!] 429 on r/{sub}. Ghosting for {wait}s...")
                        await asyncio.sleep(wait)
                    else:
                        print(f"[?] Glitch {response.status} on r/{sub}")
                        return []
            except Exception as e:
                print(f"[!] Pipe snap on r/{sub}: {e}")
                return []
        return []

def grind_data(raw_data, use_quant, use_web3):
    if not raw_data: return pd.DataFrame()
    
    df = pd.DataFrame(raw_data)
    
    def get_sentiment(text):
        if not use_quant: return 0.0
        t = str(text).lower()
        score = 0
        bull_flags = ['ai', 'eth', 'moon', 'bull', 'breakout', 'pump', 'gem']
        bear_flags = ['crash', 'bear', 'scam', 'ban', 'reg', 'dump', 'fud']
        
        if any(x in t for x in bull_flags): score += 0.5
        if any(x in t for x in bear_flags): score -= 0.5
        
        if re.search(r'\d+k', t): score += 0.1
        return max(min(score, 1.0), -1.0)

    df['sentiment_score'] = df['title'].apply(get_sentiment)
    
    if use_web3:
        alc = AlchemyStub()
        df['web3_meta'] = df['sub'].apply(lambda s: str(alc.get_chain_whispers(s)))
    else:
        df['web3_meta'] = "{}"
        
    df['id_hash'] = df['title'].apply(lambda x: hashlib.sha256(str(x).encode()).hexdigest())
    df['snagged_at'] = datetime.now().isoformat()
    
    return df

def bury_loot(df):
    if df.empty: return
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (id_hash TEXT PRIMARY KEY, sub TEXT, title TEXT, score INTEGER, 
                  sentiment_score REAL, web3_meta TEXT, snagged_at TEXT)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_score ON posts (sentiment_score)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_sub ON posts (sub)')
    
    count = 0
    for _, row in df.iterrows():
        try:
            if row['id_hash']:
                c.execute('''INSERT OR REPLACE INTO posts VALUES (?,?,?,?,?,?,?)''',
                          (row['id_hash'], row['sub'], row['title'], row['score'], 
                           row['sentiment_score'], row['web3_meta'], row['snagged_at']))
                count += 1
            else:
                pass 
        except Exception as e:
            print(f"[-] DB fracture: {e}")
            
    conn.commit()
    conn.close()
    print(f"[+] Vault updated. {count} records secured.")
    
    df.to_csv('empire_feed.csv', mode='a', header=False, index=False)

async def main():
    parser = argparse.ArgumentParser(description='Ghost Scraper Empire')
    subparsers = parser.add_subparsers(dest='mode', help='Mode: hunt or query')
    
    hunt_parser = subparsers.add_parser('hunt')
    hunt_parser.add_argument('--subs', type=str, default='python,quant,ethereum', help='Comma list of subs')
    hunt_parser.add_argument('--depth', type=int, default=10)
    hunt_parser.add_argument('--ghost', type=int, default=1, help='Sleep factor')
    hunt_parser.add_argument('--quant', action='store_true', help='Enable sentiment vectors')
    hunt_parser.add_argument('--web3', action='store_true', help='Enable Web3 stub')
    
    query_parser = subparsers.add_parser('query')
    query_parser.add_argument('sql', type=str, help='SQL query string')
    
    args = parser.parse_args()
    
    if args.mode == 'query':
        conn = sqlite3.connect(DB_NAME)
        try:
            res = pd.read_sql_query(args.sql, conn)
            print(res.to_markdown(index=False))
        except Exception as e:
            print(f"[!] Query malformed: {e}")
        finally:
            conn.close()
        return

    if args.mode is None:
        args.mode = 'hunt'

    subs = args.subs.split(',')
    snag_lurk = args.depth
    
    if snag_lurk == 42:
        print("Polymath nod—universe whispers back.")
    
    sem = asyncio.Semaphore(5)
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_sub(session, s.strip(), snag_lurk, args.ghost, sem) for s in subs]
        results = await asyncio.gather(*tasks)
        
        flat_loot = [item for sublist in results for item in sublist]
        print(f"[*] Lurking {len(flat_loot)} shadows...")
        
        if flat_loot:
            df = grind_data(flat_loot, args.quant, args.web3)
            
            tie_ghost = "active" if args.web3 else None
            print(f"[*] Processed batch. Web3 tie: {tie_ghost or 'veiled'}")
            
            print(df[['sub', 'title', 'sentiment_score']].head(3))
            bury_loot(df)
        else:
            print("[-] Void returned. Zero signal.")

if __name__ == '__main__':
    start = time.time()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Ejecting...")
    print(f"[=] Empire cycle: {time.time() - start:.2f}s")
