"""
Data Cleaning Script - Remove Noise from Election Data
Filters out table headers, metadata, and non-name entries
"""

import pandas as pd
import re
from pathlib import Path

def is_valid_politician_name(name: str) -> bool:
    """
    Check if a name is a valid politician name.
    Returns False for table headers, metadata, and other noise.
    """
    
    if not name or pd.isna(name):
        return False
    
    name = str(name).strip()
    
    # Length check
    if len(name) < 2 or len(name) > 10:
        return False
    
    # Must contain Japanese characters
    if not re.search(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]', name):
        return False
    
    # Exclude table headers and common metadata
    exclude_keywords = [
        # Table headers
        '氏名', '写真', '性別', '党派', '新旧', '年齢', '得票',
        '主な肩書', '肩書', '所属', '当落', '結果',
        
        # Metadata
        '執行理由', '任期満了', '関連情報', '選挙情報',
        '投票日', '告示日', '投票率', '有権者', '開票',
        '件', '/', 'ページ', '一覧', '結果', '速報',
        
        # Prefecture/city names
        '都道府県', '市区町村', '北海道', '青森県', '岩手県',
        '宮城県', '秋田県', '山形県', '福島県', '茨城県',
        '栃木県', '群馬県', '埼玉県', '千葉県', '東京都',
        '神奈川県', '新潟県', '富山県', '石川県', '福井県',
        
        # Election types
        '選挙', '市長選', '知事選', '議員選', '町長選', '村長選',
        
        # Common non-name patterns
        '詳細', '情報', '公報', 'データ', '記事', '特集',
        
        # Job titles that appear as separate entries
        '会社員', '無職', '経営', '代表', '職員', '元職',
        '前職', '新人', '現職', '会社役員', '団体職員',
        
        # Business/occupation descriptions (NEW - caught from data)
        '会社取締役', '取締役', '公衆浴場業', '浴場業',
        '教室主宰', '音楽教室', '塾経営', '店主',
        '自営業', '農業', '漁業', '林業', '商店主',
        '会社経営', '商店経営', '飲食店', '不動産',
        '建設業', '製造業', '運送業', '販売業',
        '理容', '美容', '整骨', '接骨', '鍼灸',
        '税理士', '行政書士', '司法書士', '弁護士',
        '医師', '歯科医', '薬剤師', '看護師',
        '教員', '講師', '塾長', '校長', '園長',
        '僧侶', '住職', '宮司', '神主',
        '農協', '漁協', '商工会', '観光協会',
        
        # Generic title patterns
        '主宰', '経営者', '代表者', '理事', '会長', '副会長',
        '顧問', '相談役', '社長', '専務', '常務',
        'NPO', '法人', '協会', '組合', '連合会'
    ]
    
    for keyword in exclude_keywords:
        if keyword in name:
            return False
    
    # Exclude if it looks like a date
    if re.search(r'\d{4}年|\d+月|\d+日', name):
        return False
    
    # Exclude if it has too many numbers
    if len(re.findall(r'\d', name)) > 3:
        return False
    
    # Exclude entries with certain symbols/patterns
    if any(char in name for char in ['（', '）', '【', '】', '/', '・・', '…']):
        # Allow some punctuation for full names
        if name.count('（') > 1 or name.count('）') > 1:
            return False
    
    # Must look like a name (kanji/hiragana/katakana with possible space)
    # Typical Japanese name pattern: 2-5 characters, possibly with space
    if re.match(r'^[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\s　]+$', name):
        return True
    
    return False


def clean_politician_data(input_file: str, output_file: str):
    """Clean the politician data by removing noise."""
    
    print("\n" + "="*80)
    print("🧹 DATA CLEANING - Removing Noise from Election Data")
    print("="*80 + "\n")
    
    # Read the CSV
    print(f"📂 Reading: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    
    print(f"📊 Original records: {len(df)}")
    
    # Filter valid names
    print("\n🔍 Filtering valid politician names...")
    df['is_valid'] = df['name'].apply(is_valid_politician_name)
    
    valid_df = df[df['is_valid']].copy()
    noise_df = df[~df['is_valid']].copy()
    
    print(f"✅ Valid politicians: {len(valid_df)} ({len(valid_df)/len(df)*100:.1f}%)")
    print(f"🗑️  Noise removed: {len(noise_df)} ({len(noise_df)/len(df)*100:.1f}%)")
    
    # Show some examples of removed noise
    print("\n📋 Sample noise removed:")
    for i, name in enumerate(noise_df['name'].head(10), 1):
        print(f"  {i}. {name}")
    
    # Drop the helper column
    valid_df = valid_df.drop('is_valid', axis=1)
    
    # Additional cleaning
    print("\n🔧 Additional cleaning...")
    
    # Remove exact duplicates
    before = len(valid_df)
    valid_df = valid_df.drop_duplicates(subset=['name', 'prefecture'], keep='first')
    after = len(valid_df)
    print(f"  • Removed {before - after} duplicate name+prefecture combinations")
    
    # Standardize party names
    party_mapping = {
        '自民': '自由民主党',
        '立憲': '立憲民主党',
        '公明': '公明党',
        '共産': '共産党',
        '維新': '日本維新の会',
        '社民': '社会民主党',
        'れいわ': 'れいわ新選組',
    }
    
    def standardize_party(party):
        if pd.isna(party) or party == '':
            return ''
        party = str(party).strip()
        for short, full in party_mapping.items():
            if short in party and full not in party:
                return full
        return party
    
    if 'party' in valid_df.columns:
        valid_df['party'] = valid_df['party'].apply(standardize_party)
        print(f"  • Standardized party names")
    
    # Sort by prefecture and name
    valid_df = valid_df.sort_values(['prefecture', 'name']).reset_index(drop=True)
    
    # Save cleaned data
    print(f"\n💾 Saving cleaned data...")
    valid_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ Saved to: {output_file}")
    
    # Statistics
    print("\n" + "="*80)
    print("📊 FINAL STATISTICS")
    print("="*80)
    print(f"\n✅ Total valid politicians: {len(valid_df)}")
    
    # Top prefectures
    print("\n📍 Top prefectures:")
    top_prefs = valid_df['prefecture'].value_counts().head(10)
    for pref, count in top_prefs.items():
        print(f"  • {pref}: {count} politicians")
    
    # Party distribution
    if 'party' in valid_df.columns:
        print("\n🏛️  Party distribution:")
        parties = valid_df['party'].value_counts().head(10)
        for party, count in parties.items():
            if party:
                print(f"  • {party}: {count} politicians")
    
    # Data quality
    if 'party' in valid_df.columns:
        with_party = valid_df['party'].notna().sum()
        print(f"\n📈 Data quality:")
        print(f"  • With party: {with_party} ({with_party/len(valid_df)*100:.1f}%)")
    
    if 'status' in valid_df.columns:
        with_status = valid_df['status'].notna().sum()
        print(f"  • With election result: {with_status} ({with_status/len(valid_df)*100:.1f}%)")
    
    if 'election_date' in valid_df.columns:
        with_date = valid_df['election_date'].notna().sum()
        print(f"  • With election date: {with_date} ({with_date/len(valid_df)*100:.1f}%)")
    
    # Sample politicians
    print("\n📋 Sample cleaned politicians:")
    for i, row in valid_df.head(10).iterrows():
        print(f"\n{i+1}. {row['name']}")
        if 'party' in row and row['party']:
            print(f"   Party: {row['party']}")
        if 'prefecture' in row:
            print(f"   Prefecture: {row['prefecture']}")
        if 'election' in row and pd.notna(row['election']):
            print(f"   Election: {row['election'][:50]}...")
        if 'status' in row and row['status']:
            print(f"   Result: {row['status']}")
    
    print("\n" + "="*80)
    print("✅ DATA CLEANING COMPLETE!")
    print("="*80 + "\n")
    
    return valid_df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean politician data")
    parser.add_argument('--input', '-i', default='politicians_from_elections.csv', help='Input CSV filename')
    parser.add_argument('--output', '-o', default='politicians_cleaned.csv', help='Output CSV filename')
    args = parser.parse_args()
    
    # Extract just filename if full path given
    from pathlib import Path
    input_file = f"data/outputs/{Path(args.input).name}"
    output_file = f"data/outputs/{Path(args.output).name}"
    
    clean_politician_data(input_file, output_file)
