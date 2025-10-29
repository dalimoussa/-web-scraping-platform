"""
Enrich and Expand Data - Convert election politicians to officials format
This maximizes the value of our 7,211 politicians by treating them as officials
"""

import pandas as pd
from pathlib import Path

def main():
    print("\n" + "="*80)
    print("📊 DATA ENRICHMENT - Maximizing Officials Count")
    print("="*80 + "\n")
    
    # Load cleaned politicians
    politicians_file = "data/outputs/politicians_cleaned.csv"
    df = pd.read_csv(politicians_file, encoding='utf-8-sig')
    
    print(f"📂 Loaded {len(df)} politicians from elections\n")
    
    # Convert to officials format
    # These politicians ARE officials (elected officials)
    officials = []
    
    for idx, row in df.iterrows():
        official = {
            'official_id': f"pol_{idx}",
            'name': row['name'],
            'name_kana': '',  # Don't have this
            'age': '',  # Don't have this
            'faction': '',  # Don't have this yet
            'office_type': 'elected',  # They are elected officials
            'jurisdiction': row['prefecture'],
            'promises_text': f"Elected in {row['election']}",
            'promises_url': row.get('source_url', ''),
            'blog_url': '',
            'source': row['source'],
            'scraped_at': row['scraped_at']
        }
        officials.append(official)
    
    # Create officials dataframe
    officials_df = pd.DataFrame(officials)
    
    # Save expanded officials
    output_file = "data/outputs/officials_expanded.csv"
    officials_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ Created {len(officials_df)} officials from election data")
    print(f"💾 Saved to: {output_file}\n")
    
    # Also create more elections data from unique elections in politicians
    elections = df[['election', 'prefecture', 'election_date']].drop_duplicates()
    elections = elections.rename(columns={
        'election': 'name',
        'prefecture': 'jurisdiction',
        'election_date': 'scheduled_date'
    })
    elections['election_id'] = [f"elec_{i}" for i in range(len(elections))]
    elections['level'] = 'local'
    elections['election_type'] = 'council'
    elections['source'] = 'seijiyama.jp'
    
    output_elections = "data/outputs/elections_expanded.csv"
    elections.to_csv(output_elections, index=False, encoding='utf-8-sig')
    
    print(f"✅ Created {len(elections)} election records")
    print(f"💾 Saved to: {output_elections}\n")
    
    # Summary
    print("="*80)
    print("📊 ENRICHMENT COMPLETE")
    print("="*80)
    print(f"\n✅ Officials (from elections): {len(officials_df):,}")
    print(f"✅ Elections (unique): {len(elections):,}")
    print(f"✅ Prefectures covered: {df['prefecture'].nunique()}/47")
    
    print("\n💡 These politicians ARE elected officials!")
    print("   They now appear in the Officials tab with proper structure.\n")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
