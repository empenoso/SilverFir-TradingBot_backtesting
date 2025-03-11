# SilverFir-TradingBot_backtesting
Когда закончил писать [механизм своего торгового робота](https://github.com/empenoso/SilverFir-TradingBot) обнаружил, что самое главное всё таки не сам механизм, а стратегия, по которой этот механизм будет работать.
Первый тесты на истории показали что с доходностью и тем более с тем как доходность портфеля компенсирует принимаемый риск (коэффициент Шарпа) проблемы, но неудачный опыт тоже опыт, поэтому решил описать его в статье.
Первый и самый важный вопрос - при помощи чего проводить тесты торговой стратегии на исторических данных? В какой программе или при помощи какой библиотеки создавать стратегию и потом прогонять её на истории? 

⚠️ Новые модули будут загружаться по мере написания и тестирования. 

## Подробное описание в статьях:

1. Мой первый и неудачный опыт поиска торговой стратегии внутри дня для Московской биржи (библиотека backtrader):
   * [Хабр](https://habr.com/ru/articles/857402/)
   * [Смартлаб](https://smart-lab.ru/mobile/topic/1083556/)     

2. Тестирование торговой стратегии нового индикатора Джона Ф. Элерса на Python для дневных данных Мосбиржи через библиотеку backtesting.py
   * [Хабр](https://habr.com/ru/articles/887440/)
   * [Смартлаб](https://smart-lab.ru/mobile/topic/1126711/)

3. ~~Фундаментальный скринер~~
   * [Хабр](https://habr.com/ru/users/empenoso/)
   * [Смартлаб](https://smart-lab.ru/mobile/users/empenoso/blog/)
