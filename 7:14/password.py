import re


def validate_password(password):
    # 비밀번호 조건 정의
    if len(password) < 8:
        return 0
    if not re.search(r"[a-z]", password):
        return 0
    if not re.search(r"[A-Z]", password):
        return 0
    if not re.search(r"[0-9]", password):
        return 0
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return 0

    return 1


def main():
    while True:
        password = input("비밀번호를 입력하세요 (!quit 입력 시 종료): ")

        if password == "!quit":
            print("프로그램을 종료합니다. 안녕히 가세요!")
            break

        if validate_password(password):
            print("사용 가능한 비밀번호입니다.")
        else:
            print(
                "비밀번호는 영문 소문자, 대문자, 숫자, 기호를 각각 최소 1개 이상 포함해야 합니다."
            )


if __name__ == "__main__":
    main()
