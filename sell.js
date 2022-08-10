Function cs();
Begin
    begin_day := IntToDate({day});
    begin_time := '{time}';
    point := {point};

    ret := array();
    stock_list := getbk('A股');
    stock_list::begin
        stock_code := mcell;
        stock_name := stockName(stock_code);

        if not (stock_code like 'SZ|SH') then
            continue;

        if stock_name like 'ST|退' then
            continue;

        if not is_trade_day(begin_day, stock_code) then
            continue;

        setsysparam(pn_stock(), stock_code);
        day := StockEndTPrevNDay(begin_day, -1);
        str_day := DateToStr(day);
        卖出 := 计算卖出(stock_name, stock_code, day, begin_time);
        assert(卖出[0] <> 0);
        arr := array(('名称':stock_name, '代码':stock_code,
            '卖出价':floatn(卖出[0] * (1 + point / 100), 3), '卖出日期':卖出[1], '卖出时间':卖出[2]));
        ret &= arr;
    end
    return exportjsonstring(ret);
End;

function 计算卖出(stock_name, stock_code, day, begin_time);
begin
    while True do
    begin
        ret := 计算某一日卖出(stock_name, stock_code, day, begin_time);
        if ret[0] = 0 then
        begin
            with *,array(pn_Stock():stock_code, PN_Cycle():cy_day()) do
                day := StockEndTPrevNDay(day, -1);
        end
        else
            return ret;
    end
end

function 计算某一日卖出(stock_name, stock_code, day, begin_time);
begin
    if day = date() then
    begin
        with *,array(pn_Stock():stock_code, pn_rate():2, pn_rateday():day) do
        begin
            last_close := stockclose(StockEndTPrevNDay(day, 1));
            last_day := DateToStr(StockEndTPrevNDay(day, 1));
            return array(last_close, last_day, begin_time);
        end
    end
    sell_price := 0;
    sell_day := 0;
    sell_time := 0;
    str_day := DateToStr(day);

    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        当日涨停价 := StockZtClose(day);
    end

    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"]
        from markettable datekey day+StrToTime(begin_time) to day+0.99999 of DefaultStockID() end;
    end

    for idx in data do
    begin
        if data[idx]['close'] <> 当日涨停价 then
        begin
            sell_price := data[idx]['close'];
            sell_day := str_day;
            sell_time := data[idx]['时间'];
            break;
        end
    end
    return array(sell_price, sell_day, sell_time);
end

function count_ratio(value1, value2);
begin
    if value2 = 0 then
        return 0;
    return floatn((value1 / value2 - 1) * 100, 3);
end

Function is_trade_day(day,stock_code);
Begin
    with *,array(pn_Stock():stock_code,PN_Date():day,pn_rate():0,pn_rateday():day,PN_Cycle():"日线") do
    begin
        if not spec(isTradeDay(day),stock_code) then
            return false;

        if IsStockGoDelistingPeriod(day) then
            return false;

        if IsST_3(day)=1 then
            return false
    end
    return true;
End;
