# 사용자 입력을 받아 그대로 출력하는 프로그램
def main():
    while True:  # 무한 루프를 시작합니다.
        user_input = input("문장을 입력하세요 (!quit 입력시 종료):")  # 사용자 입력 받기

        if user_input == "!quit":  # 종료 조건 확인
            print("프로그램을 종료합니다. 안녕히 가세요!")
            break  # 루프를 종료하고 프로그램을 끝냅니다.

        print("입력하신 문장은:", user_input)  # 입력받은 문장 출력


if __name__ == "__main__":
    main()
