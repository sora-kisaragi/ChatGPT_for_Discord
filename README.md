# Discord ChatGPT/Ollama Bot

OpenAI ChatGPT API �� Ollama API �̗����ɑΉ����� Discord Bot �ł��B

## ����

- **����AI�Ή�**: OpenAI ChatGPT �� Ollama �̗������T�|�[�g
- **�`�����l���ʉ�b�Ǘ�**: �`�����l�����ƂɓƗ�������b����
- **�ݒ�\�ȃv�����v�g**: �`�����l�����Ƃ�AI�̐ݒ���J�X�^�}�C�Y
- **���ϐ��ɂ��ݒ�**: ���S�ŊȒP�Ȑݒ�Ǘ�
- **�G���[�n���h�����O**: ���S�ȃG���[�����ƃ��O�@�\
- **�R�}���h�T�|�[�g**: �L�x�ȃ{�b�g�R�}���h

## �K�v����

- Python 3.8�ȏ�
- Discord Bot Token
- OpenAI API Key (OpenAI�g�p��) �܂��� Ollama �T�[�o�[ (Ollama�g�p��)

## �C���X�g�[��

1. ���|�W�g�����N���[��
```bash
git clone <repository-url>
cd ChatGPT_for_Discord
```

2. �ˑ��֌W���C���X�g�[��
```bash
pip install -r requirements.txt
```

3. ���ݒ�
```bash
cp .env.example .env
# .env �t�@�C����ҏW���Đݒ���L��
```

## �ݒ�

### ���ϐ��ݒ� (.env �t�@�C��)

```env
# Discord�ݒ�
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_IDS=123456789012345678,987654321098765432

# AI �v���o�C�_�[�ݒ�
AI_PROVIDER=ollama  # "openai" �܂��� "ollama"

# OpenAI�ݒ� (AI_PROVIDER=openai �̏ꍇ)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Ollama�ݒ� (AI_PROVIDER=ollama �̏ꍇ)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# ����AI�ݒ�
MAX_HISTORY=10
TEMPERATURE=0.7
```

### Ollama �Z�b�g�A�b�v

1. [Ollama](https://ollama.ai/) ���C���X�g�[��
2. ���f�����_�E�����[�h:
```bash
ollama pull llama3.1
```
3. �T�[�o�[���N��:
```bash
ollama serve
```

## ���s

```bash
python src/ChatGPT_Discord.py
```

## �g�p���@

### ��{�R�}���h

- `/gpt [���b�Z�[�W]` �܂��� `/ai [���b�Z�[�W]` - AI�ƑΘb
- `/reset` - ��b���������Z�b�g���A�ݒ��ύX
- `/show` - ���݂̐ݒ��\��
- `/stats` - ��b���v��\��
- `/help` - �w���v��\��

### �g�p��

```
/ai ����ɂ���
/gpt �����̓V�C�͂ǂ��ł����H
/reset
/show
/stats
```

## �v���W�F�N�g�\��

```
ChatGPT_for_Discord/
������ src/
��   ������ ChatGPT_Discord.py     # ���C���{�b�g�t�@�C��
��   ������ ai_client.py           # AI API �N���C�A���g
��   ������ config.py              # �ݒ�Ǘ�
��   ������ conversation_manager.py # ��b�����Ǘ�
��   ������ check_channels.py      # �`�����l���m�F�@�\
��   ������ utils.py               # ���[�e�B���e�B�֐�
������ requirements.txt           # �ˑ��֌W
������ .env.example              # ���ϐ��e���v���[�g
������ start.bat                 # Windows�N���X�N���v�g
������ start.sh                  # Linux/Mac�N���X�N���v�g
������ README.md                 # ���̃t�@�C��
```

## ��ȉ��P�_

1. **�A�[�L�e�N�`���̉��P**
   - ���W���[�����ƃN���X�x�[�X�݌v
   - �֐S�̕���
   - �ė��p�\�ȃR���|�[�l���g

2. **AI API �Ή�**
   - OpenAI �� Ollama �̓���C���^�[�t�F�[�X
   - �ݒ�ɂ�铮�I�؂�ւ�
   - �񓯊������Ή�

3. **�Z�L�����e�B����**
   - ���ϐ��ɂ��ݒ�Ǘ�
   - API �L�[�̈��S�ȕۑ�

4. **�G���[�n���h�����O**
   - ��I�ȃG���[����
   - ���O�@�\
   - ���[�U�[�t�����h���[�ȃG���[���b�Z�[�W

5. **�@�\�g��**
   - �`�����l���ʉ�b�Ǘ�
   - ���v���\��
   - �^�C���A�E�g����

## ���C�Z���X

���̃v���W�F�N�g��[MIT���C�Z���X](LICENSE.md)�̂��ƂŌ��J����Ă��܂��B

## �v��

�v�����N�G�X�g��C�V���[�̕񍐂����}���܂��B