while True:
    user_o_producer= input("Sei un 'user' o un 'producer'? ").strip().lower()
    if user_o_producer == "user":
        from consumer import main as consumer_main

        consumer_main()
        break
    elif user_o_producer == "producer":
        from producer import main as producer_main

        producer_main()
        break
    else:
        print("❌ Scelta non valida. Riprova.")