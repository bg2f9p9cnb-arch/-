# 사회초년생 금융용어 카드뉴스 자동 게시기 (@googogogo011)

매일 오전 9시와 저녁 7시, 한국은행 『경제금융용어 800선』의 용어 하나씩(하루 2개) 피그마 템플릿 모양의 카드 5장으로 만들어 인스타그램에 자동으로 올립니다.
서버 없이 GitHub Actions(무료)로 돌아가요.

- 카드 문구는 `content_bank.json` 에 **60일 치를 미리 써뒀어요.** API 비용 0원.
- 다 떨어지기 일주일 전부터 GitHub Actions 화면에 경고가 떠요. 그때 Claude에게 "content_bank.json 더 채워줘"라고 하면 돼요.
- `ANTHROPIC_API_KEY` 를 등록하면, 써둔 문구가 떨어진 뒤 Claude가 자동으로 새로 만들어요. (선택)

## 카드 구성 (피그마 템플릿 기준)
| 장 | 피그마 프레임 | 내용 |
|---|---|---|
| 1 | 썸네일 | 배경 + "오늘의 금융용어 No.N" + 제목 2줄 + 해시태그 |
| 2 | 본문 1 | '금융용어 사전' 카드 + "이게 뭐예요?" |
| 3 | 본문 2 | 쉬운 비유 + 사회초년생 예시 |
| 4 | 본문 2 | 이것만 기억해요 + 한 줄 요약 |
| 5 | 마지막장 | "팔로우하고 금융상식 얻어가세요!" + 프로필 |

## 설정 순서 (iPad 기준)

### 1. 파일 올리기
1. 받은 zip을 **파일 앱**에서 탭해서 압축을 풀어요.
2. GitHub 저장소 페이지 → **Add file → Upload files** → **choose your files**
3. 풀린 폴더 안 파일을 **전부 선택**해서 올리고 **Commit changes**를 눌러요.
   (`preview` 폴더는 안 올려도 돼요.)

### 2. 자동 실행 파일 만들기 (폴더 이름이 점으로 시작해서 직접 만들어야 해요)
1. 저장소 페이지 → **Add file → Create new file**
2. 파일 이름 칸에 `.github/workflows/daily.yml` 을 그대로 입력해요.
3. 따로 받은 `daily.yml` 내용을 전부 복사해서 붙여넣고 **Commit changes**를 눌러요.

### 3. 비밀값 등록
저장소 → **Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 |
|---|---|
| `IG_ACCESS_TOKEN` | Meta 개발자 페이지에서 받은 인스타 토큰 |
| `IG_USER_ID` | 17841로 시작하는 숫자 (선택) |
| `GH_PAT` | (선택) 토큰 자동 갱신용, 아래 5번 |
| `ANTHROPIC_API_KEY` | (선택) 문구 자동 생성용 |

같은 화면의 **Variables** 탭(선택): `PROFILE_NAME` = 마지막 장 프로필 이름 (기본 `지안`)

### 4. 권한 켜고 첫 테스트
1. **Settings → Actions → General → Workflow permissions → Read and write permissions** 선택 후 Save
2. **Actions** 탭 → `daily-cardnews` → **Run workflow** → "미리보기만 만들기" 체크 → 실행
3. 끝나면 실행 결과 하단 **preview**를 내려받아 확인
4. 괜찮으면 체크 없이 한 번 더 실행 → 인스타에 바로 올라가요 (이게 첫 게시물)

이후로는 **매일 오전 9시 정각**에 자동으로 올라가요.
- 8시 17분에 미리 시작해 카드를 만들어 두고 9:00까지 기다렸다가 올려요.
- 9시 47분 예비 실행은 아침 실행이 실패했을 때만 올려요. 하루 두 번 올라가지 않아요.

### 5. 토큰 자동 갱신 (권장)
인스타 토큰은 60일 뒤 만료돼요. 매월 1일·15일에 자동으로 갱신하려면:
1. GitHub → 프로필 → Settings → Developer settings → **Fine-grained tokens → Generate new token**
2. Repository access: 이 저장소만 / Permissions → **Secrets: Read and write**
3. 만든 토큰을 `GH_PAT` 으로 등록

## 꾸미기
- **배경 사진**: `bg_` 로 시작하는 이름의 세로 사진(예: `bg_1.jpg`)을 저장소에 올리면 표지·마지막 장 배경으로 돌아가며 써요. 없으면 색 번짐 배경을 자동으로 만들어요.
- **프로필 사진**: `profile.jpg` 를 바꿔 올리면 돼요.
- **디자인**: `render.py` 에 피그마 좌표 그대로 옮겨져 있어요.

## 파일
| 파일 | 역할 |
|---|---|
| `content_bank.json` | 미리 써둔 카드 문구 60개 (순서대로 게시) |
| `terms.json` | PDF에서 뽑은 용어 778개 원문 |
| `run_daily.py` | 전체 실행 |
| `content.py` | 문구 고르기·생성, 캡션 |
| `render.py`, `backgrounds.py` | 카드 이미지 만들기 |
| `instagram.py`, `refresh_token.py` | 인스타 게시, 토큰 갱신 |
| `state.json` | 올린 용어 기록 (자동으로 바뀌어요) |
| `Pretendard-*.otf` | 폰트 (OFL 라이선스) |

## 저작권 메모
카드에는 한국은행 원문을 그대로 옮기지 않고 새로 풀어 쓴 문장만 들어가며 출처를 표기해요.
상업적으로 운영할 계획이라면 한국은행 경제교육실(02-759-5316)에 이용 범위를 한 번 문의해두면 안전해요.
