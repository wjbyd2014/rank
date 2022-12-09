Function 龙回头();
Begin
    day := IntToDate({day});
    ret := array();
    stock_list := getbk('A股');
    stock_list::begin
        stock_code := mcell;
        stock_name := stockName(stock_code);

        if not (stock_code like 'SZ|SH') then
            continue;

        //if stock_name like '退' then
            //continue;

        if not is_trade_day(day, stock_code) then
            continue;

        with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
        begin
            is_zt := IsST_3(day);
            prev_day := StockEndTPrevNDay(day, 1);
            if prev_day = 0 then
                continue;

            prev_high := StockHigh4(prev_day);
            prev_zt := StockZtClose(prev_day);
            if prev_high = prev_zt then
                continue;

            cur_high := StockHigh4(day);
            cur_zt := StockZtClose(day);
            if cur_high <> cur_zt then
                continue;
        end

        买入 := 计算买入(stock_name, stock_code, day);
        if 买入[0] = 0 then
            continue;

        涨停板 := 计算涨停板(stock_name, stock_code, day);
        if is_zt = 0 then
        begin
            大涨 := 计算大涨(stock_name, stock_code, day);
            if 大涨[6] = 0 then
                continue;
        end
        else
            大涨 := zeros(8);

        上市天数 := 计算自定义上市天数(stock_code, day);
        ret &= array(('名称':stock_name, '代码':stock_code,
            'is_st':is_zt, '上市天数':上市天数,
            '买入时间':买入[1], '买入价':买入[0], '买入金额':买入[2],
            '10日涨停数':涨停板[0], '20日涨停数':涨停板[1],
            '30日涨停数':涨停板[2], '40日涨停数':涨停板[3],
            '10日最大大涨幅度':大涨[0], '10日最大大涨日期':大涨[1],
            '20日最大大涨幅度':大涨[2], '20日最大大涨日期':大涨[3],
            '30日最大大涨幅度':大涨[4], '30日最大大涨日期':大涨[5],
            '40日最大大涨幅度':大涨[6], '40日最大大涨日期':大涨[7]));
    end
    return exportjsonstring(ret);
End;

function 计算涨停板(stock_name, stock_code, day);
begin
    num1 := 0;
    num2 := 0;
    num3 := 0;
    num4 := 0;

    num := 0;
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        for i := 1 to 40 do
        begin
            one_day := StockEndTPrevNDay(day, i);
            if one_day = 0 then
                break;

            if StockIsZt(one_day) then
                num += 1;

            if i = 10 then
                num1 := num;
            else if i = 20 then
                num2 := num;
            else if i = 30 then
                num3 := num;
            else if i = 40 then
                num4 := num;
        end
        return array(num1, num2, num3, num4);
    end
end

function 计算大涨(stock_name, stock_code, day);
begin
    num1 := 0;
    day1 := '';
    num2 := 0;
    day2 := '';
    num3 := 0;
    day3 := '';
    num4 := 0;
    day4 := '';
    max_incr := 0;
    max_incr_day := 0;
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        ret := 0;
        for i := 1 to 40 do
        begin
            one_day := StockEndTPrevNDay(day, i);
            if one_day = 0 then
                break;
                
            str_one_day := DateToStr(one_day);
            prev_one_day := StockEndTPrevNDay(day, i + 1);
            if prev_one_day = 0 then
                break;

            one_day_high := StockHigh4(one_day);
            prev_day_close := StockClose(prev_one_day);
            one_day_high_incr := count_ratio(one_day_high, prev_day_close);

            if one_day_high_incr > 7 and one_day_high_incr > max_incr then
            begin
                max_incr := one_day_high_incr;
                max_incr_day := str_one_day;
            end

            if i = 10 then
            begin
                num1 := max_incr;
                day1 := max_incr_day;
            end
            else if i = 20 then
            begin
                num2 := max_incr;
                day2 := max_incr_day;
            end
            else if i = 30 then
            begin
                num3 := max_incr;
                day3 := max_incr_day;
            end
            else if i = 40 then
            begin
                num4 := max_incr;
                day4 := max_incr_day;
            end
        end
        return array(num1, day1, num2, day2, num3, day3, num4, day4);
    end
end

function 计算买入(stock_name, stock_code, day);
begin
    buy_price := 0;
    buy_time := 0;

    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        当日涨停价 := StockZtClose(day);
    end

    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"],
        ['amount'],
        ['low']
        from markettable datekey day to day+0.99999 of DefaultStockID() end;
    end

    第一个非涨停价 := 0;
    for idx in data do
    begin
        if data[idx]['close'] <> 当日涨停价 then
        begin
            第一个非涨停价 := data[idx]['close'];
        end
        else
        begin
            if data[idx]['low'] <> 当日涨停价 then
                 return array(当日涨停价, data[idx]['时间'], 5000000);

            if 第一个非涨停价 <> 0 then
            begin
                buy_price := data[idx]['close'];
                buy_time := data[idx]['时间'];
                break;
            end
        end
    end
    return array(buy_price, buy_time, 5000000);
end

function 计算自定义上市天数(stock_code, day);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        当前日 := DateToInt(day);
        上市日 := FundGoMarketDate();
        if 当前日 = 上市日 then
            return 0;

        上市天数 := StockGoMarketDays();
        assert(上市天数 > 0);

        num := 1;
        while true do
        begin
            下一日 := StockEndTPrevNDay(IntToDate(上市日), -num);
            str_next_day := DateToStr(下一日);

            if 下一日 = day then
                return 0;

            if stockiszt2(下一日) then
                num += 1;
            else
                break;
        end
    end
    return day - 下一日;
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
    end
    return true;
End;
