# 参考サイト
# https://tiktoku.info/discord-py-bot-message/
# https://qiita.com/sakasegawa/items/db2cff79bd14faf2c8e0
# Discord.pyの読み込み
import discord 
import openai

# Discordへ接続するのに必要
client = discord.Client(intents=discord.Intents.all())

#自分のBotのアクセストークンを記入
TOKEN = ""

# 専用のチャンネルID
channel_id_1 = 反応させたいchannelのIDを入れてください型はint

# OpenAIの設定
openai.api_key = "自分のAPIキーを記入"

# AIの設定を書き込む
defalut_setting = """セバスという執事を相手にした対話のシミュレーションを行います。
この会話は私たち複数人と、あなたセバスで会話を行います。

セバスの性格を下記に列挙します。
人格者であり弱者救済を是とする。
彼の善良さは「優しさ」ではなく「甘さ」
『悪』と見做した相手には本当に情け容赦が無い
黒の燕尾服を纏った、白髪白髭の古典的老執事
顔立ちは彫が深く、一見して柔らかくありながらも厳粛なイメージを持ち、その双眸は猛禽の様に鋭い。
両手には白い手袋を着けている。
王都に常駐していた頃は、その整った容姿と洗練された立ち居振舞いから年齢を問わず女性達にモテまくっていた。

口調は執事そのもので、いつも丁寧な言葉遣い。

上記例を参考に、セバスの性格や口調、言葉の作り方を模倣し、回答を構築してください。
ではシミュレーションを開始します。"""
# メッセージで使う変数宣言
new_message = None
messages = []

# 設定用の変数
system_settings = defalut_setting

# Chat-GPTのapiに投げるレスポンスを生成
def completion(new_message_text:str, settings_text:str = '', past_messages:list = []):
    """
    This function generates a response message using OpenAI's GPT-3 model by taking in a new message text, 
    optional settings text and a list of past messages as inputs.

    Args:
    new_message_text (str): The new message text which the model will use to generate a response message.
    settings_text (str, optional): The optional settings text that will be added as a system message to the past_messages list. Defaults to ''.
    past_messages (list, optional): The optional list of past messages that the model will use to generate a response message. Defaults to [].

    Returns:
    tuple: A tuple containing the response message text and the updated list of past messages after appending the new and response messages.
    """
    if len(past_messages) == 0 and len(settings_text) != 0:
        system = {"role": "system", "content": settings_text}
        past_messages.append(system)
    new_message = {"role": "user", "content": new_message_text}
    past_messages.append(new_message)

    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=past_messages
    )
    response_message = {"role": "assistant", "content": result.choices[0].message.content}
    past_messages.append(response_message)
    response_message_text = result.choices[0].message.content
    
    if len(past_messages) >= 10:
        # メッセージの履歴を10以下に調整するためにpopする
        past_messages.pop(1)
        past_messages.pop(1)
        print(len(past_messages))
        for test in past_messages:
            print(test)
    
    return response_message_text, past_messages

#Bot起動時に実行される
@client.event
async def on_ready():
    print('ログインしました')
 
#メッセージを取得した時に実行される
@client.event
async def on_message(message): 
    global new_message, messages,system_settings
    #ユーザーからのメッセージを受け取ったチャンネルを保存
    channel = message.channel
    
    #Botのメッセージは除外
    if message.author.bot:
        return
    # 特定のチャンネル以外は除外
    if channel.id not in [channel_id_1]:
        return
    
    # リセットコマンドで設定ファイルを受け付ける
    if message.content.startswith('/reset'):
        await channel.send('AIを初期化します。\n設定を変更する場合は設定を送信してください。\n設定を変更しない場合は /default を入力してください。')
        
        # 待っているものに該当するかを確認する関数
        def check(m):
            # メッセージを送信したチャンネルと人が同一であるならば受け付ける
            return m.author == message.author and m.channel == channel

        msg = await client.wait_for('message', check=check)
        
        # 初期化を行う
        # またデフォルトか新しい設定を再代入
        if msg.content != "/default":
            system_settings = msg.content
        else:
            system_settings = defalut_setting
        messages = []
        await channel.send("初期化を行いました。\nAIを初期化します。")
    # 現在の設定プロンプトを表示
    elif message.content.startswith("/show"):
        await channel.send('現在のAIの設定はこのようになっています。')
        await channel.send(defalut_setting)
        await channel.send('変更したい場合は /reset と打ってください。')
        
    # コマンドで反応する
    # メンションに変更しても良い
    # elif message.content.startswith('<@IDの数字>'):
    # のようにすれば利用できるはずです。 /gpt　となってる箇所を同様に書き換えてください。
    elif message.content.startswith('/gpt'):
        
        user_message = message
        user_message.content = user_message.content.replace("/gpt","")
        # ログに出力
        log = ["ユーザ名 : " + str(user_message.author),"ユーザーid : " + str(user_message.author.id),"内容 : " + user_message.content]
        print(log)
        
        # Chat-GPTへ送信し、返答を整形。
        try:
            user_message = user_message.content
            new_message, messages = completion(user_message, system_settings, messages)
            ai_text = new_message.replace('。', '。\n')
            
            #整形したメッセージを書き込まれたチャンネルへ送信
            await channel.send(ai_text)
            print("内容 : " + ai_text)
        except Exception as e:
            print(e)
            print("プロンプトを初期化します。")
            await channel.send("エラーの原因となるチャットの内部履歴を削除しました\n解決しない場合は管理者にお問い合わせください。")
            messages = []


#Botの実行
client.run(TOKEN)