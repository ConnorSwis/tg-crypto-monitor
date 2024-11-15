from tg_crypto_monitor.main import main


def start():
    main()


def dev():
    main(reload=True)
