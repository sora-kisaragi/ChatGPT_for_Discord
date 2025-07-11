"""
チャンネルアクセス診断スクリプト
"""
import os
import discord
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def check_channel_access():
    """チャンネルアクセスを詳細に診断"""
    
    token = os.getenv('DISCORD_TOKEN')
    channel_ids_str = os.getenv('DISCORD_CHANNEL_IDS', '')
    channel_ids = [int(x.strip()) for x in channel_ids_str.split(",") if x.strip()]
    
    print("=" * 60)
    print("チャンネルアクセス診断")
    print("=" * 60)
    print(f"設定されたチャンネルID: {channel_ids}")
    
    # 最小限のインテント設定
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"\n🤖 ボット: {client.user}")
        print(f"🏰 参加サーバー数: {len(client.guilds)}")
        
        # 全サーバーとチャンネルを表示
        for guild in client.guilds:
            print(f"\n📡 サーバー: {guild.name} (ID: {guild.id})")
            print(f"   メンバー数: {guild.member_count}")
            print(f"   ボットの権限: オーナー={guild.owner_id == client.user.id}")
            
            # テキストチャンネル一覧
            text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
            print(f"   📝 テキストチャンネル数: {len(text_channels)}")
            
            for channel in text_channels[:10]:  # 最初の10個のみ表示
                permissions = channel.permissions_for(guild.me)
                print(f"      #{channel.name} (ID: {channel.id}) - 読取:{permissions.read_messages} 送信:{permissions.send_messages}")
        
        print(f"\n🔍 指定チャンネルの詳細確認:")
        for channel_id in channel_ids:
            channel = client.get_channel(channel_id)
            if channel:
                permissions = channel.permissions_for(channel.guild.me)
                print(f"✅ チャンネル: #{channel.name} (ID: {channel_id})")
                print(f"   サーバー: {channel.guild.name}")
                print(f"   権限 - 表示:{permissions.view_channel} 読取:{permissions.read_messages} 送信:{permissions.send_messages}")
                
                # テストメッセージ送信
                try:
                    test_msg = await channel.send("🔧 **アクセステスト** - ボットは正常にこのチャンネルにアクセスできます！")
                    print(f"   ✅ テストメッセージ送信成功")
                    await asyncio.sleep(2)
                    await test_msg.delete()
                    print(f"   🗑️ テストメッセージ削除完了")
                except Exception as e:
                    print(f"   ❌ メッセージ送信エラー: {e}")
            else:
                print(f"❌ チャンネルID {channel_id} が見つかりません")
                
                # 全チャンネルから検索
                found = False
                for guild in client.guilds:
                    for ch in guild.channels:
                        if ch.id == channel_id:
                            print(f"   ⚠️ チャンネルは存在しますが、アクセス権限がありません")
                            print(f"   チャンネル: #{ch.name} (サーバー: {guild.name})")
                            found = True
                            break
                    if found:
                        break
                
                if not found:
                    print(f"   🔍 このチャンネルIDは存在しないか、ボットがそのサーバーに招待されていません")
        
        print(f"\n診断完了。5秒後に終了します...")
        await asyncio.sleep(5)
        await client.close()
    
    try:
        await client.start(token)
    except Exception as e:
        print(f"❌ 接続エラー: {e}")

if __name__ == "__main__":
    asyncio.run(check_channel_access())