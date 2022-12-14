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

        if stock_code[3:4] = '30' or stock_code[3:4] = '68' then
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

            yzb := StockIsZt2(day);
            if yzb = 1 then
                continue;

            ma3上涨起始日 := count_ma_start_day(day, 3);
            str_ma3上涨起始日 := DateToStr(ma3上涨起始日);
            ma3涨停 := count_ma3_zt(stock_name, stock_code, day, ma3上涨起始日);

            highest10 := count_highest_high(stock_name, stock_code, day, 10);
            highest_incr := count_ratio(cur_zt, highest10[0]);

            dt_num4 := count_dt(stock_name, stock_code, day, 4);
            上次涨停信息 := count_last_zt(stock_name, stock_code ,day, 7);
        end

        买入 := 计算买入(stock_name, stock_code, day, cur_zt);
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
            '买入时间':买入[1], '买入价':cur_zt, '原始金额':买入[0],
            '本日涨停价和10日内最高最高价涨幅':highest_incr,
            '10日内最高最高价日期':highest10[1],
            '4日内最低价跌停次数':dt_num4,
            'ma3上涨起始日':str_ma3上涨起始日,
            'ma3涨停数量':ma3涨停[0], 'ma3最高价涨停数量':ma3涨停[1],
            '200日涨停数':涨停板[4],
            '7日内上次涨停日期':上次涨停信息[0],
            '上次涨停距今几日':上次涨停信息[1],
            '上次涨停距今最高价最高涨幅':上次涨停信息[2],
            '上次涨停距今累计涨幅':上次涨停信息[3],
            '上次涨停距今阳线个数':上次涨停信息[4],
            'is_st':is_zt, '上市天数':上市天数,
            '10日涨停数':涨停板[0], '20日涨停数':涨停板[1],
            '30日涨停数':涨停板[2], '40日涨停数':涨停板[3],
            '10日最大大涨幅度':大涨[0], '10日最大大涨日期':大涨[1],
            '20日最大大涨幅度':大涨[2], '20日最大大涨日期':大涨[3],
            '30日最大大涨幅度':大涨[4], '30日最大大涨日期':大涨[5],
            '40日最大大涨幅度':大涨[6], '40日最大大涨日期':大涨[7]));
    end
    return exportjsonstring(ret);
End;

function count_last_zt(stock_name, stock_code ,day, num);
begin
    上市日 := FundGoMarketDate();
    last_zt_day := '';
    num1 := 0;
    num2 := 0;
    num3 := 0;
    num4 := 0;
    for i := 1 to num + 1 do
    begin
        one_day := StockEndTPrevNDay(day, i);
        if DateToInt(one_day) < 上市日 then
            break;

        prev_one_day := StockEndTPrevNDay(day, i + 1);
        if prev_one_day = 0 then
            break;

        if MonthsBetween(one_day, prev_one_day) > 1 then
            break;

        str_one_day := DateToStr(one_day);
        str_prev_one_day := DateToStr(prev_one_day);
        if StockIsZt(one_day) then
        begin
            last_zt_day := DateToStr(one_day);
            one_day_close := StockClose(one_day);
            prev_day := StockEndTPrevNDay(day, 1);
            prev_day_close := StockClose(prev_day);
            num3 := count_ratio(prev_day_close, one_day_close);
            break;
        end

        num1 += 1;
        one_day_high := StockHigh4(one_day);
        prev_day_close := StockClose(prev_one_day);
        incr_ratio := count_ratio(one_day_high, prev_day_close);
        if incr_ratio > num2 then
            num2 := incr_ratio;

        one_day_close := StockClose(one_day);
        one_day_open := StockOpen4(one_day);
        if one_day_close > one_day_open then
            num4 += 1;
    end
    if last_zt_day = '' then
        return array('', 0, 0, 0, 0);
    else
        return array(last_zt_day, num1, num2, num3, num4);
end

function count_dt(stock_name, stock_code, day, num);
begin
    上市日 := FundGoMarketDate();
    ret := 0;
    for i := 1 to num do
    begin
        one_day := StockEndTPrevNDay(day, i);
        str_one_day := DateToStr(one_day);

        if DateToInt(one_day) < 上市日 then
            break;

        one_day_dt := StockDtClose(one_day);
        one_day_low := StockLow4(one_day);
        if one_day_low = one_day_dt then
            ret += 1;
    end
    return ret;
end

function count_highest_high(stock_name, stock_code, day, num);
begin
    data := nday(num + 1, '时间',datetimetostr(sp_time()), '当日高价',high());
    assert(length(data) > 1);

    highest_price := 0;
    highest_price_day := '';
    for idx := 0 to length(data) - 2 do
    begin
        if data[idx]['当日高价'] > highest_price then
        begin
            highest_price := data[idx]['当日高价'];
            highest_price_day := data[idx]['时间'];
        end
    end
    return array(highest_price, highest_price_day);
end

function count_ma3_zt(stock_name, stock_code, day, begin_day);
begin
    上市日 := FundGoMarketDate();
    i := 1;
    num1 := 0;
    num2 := 0;
    while True do
    begin
        one_day := StockEndTPrevNDay(day, i);
        str_one_day := DateToStr(one_day);

        if DateToInt(one_day) < 上市日 then
            break;

        if one_day < begin_day then
            break;

        if StockIsZt(one_day) = 1 then
            num1 += 1;

        one_day_high := StockHigh4(one_day);
        one_day_zt := StockZtClose(one_day);
        if one_day_high = one_day_zt then
            num2 += 1;
        i += 1;
    end
    return array(num1, num2);
end

function count_ma_start_day(day, num);
begin
    上市日 := FundGoMarketDate();
    ret := 0;
    i := 2;
    last_ma := ref(ma(close(), num), 1);
    while True do
    begin
        one_day := StockEndTPrevNDay(day, i);
        if DateToInt(one_day) < 上市日 then
            break;

        one_day_close := StockClose(one_day);
        one_ma := ref(ma(close(), num), i);
        if one_ma <= last_ma then
        begin
            i += 1;
            last_ma := one_ma;
        end
        else
            break;
    end
    return StockEndTPrevNDay(day, i - 1);
end

function 计算涨停板(stock_name, stock_code, day);
begin
    num1 := 0;
    num2 := 0;
    num3 := 0;
    num4 := 0;
    num5 := 0;

    num := 0;
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        for i := 1 to 200 do
        begin
            one_day := StockEndTPrevNDay(day, i);
            if one_day = 0 then
                break;

            if StockIsZt(one_day) then
                num += 1;

            if i = 10 then
            begin
                num1 := num;
                num2 := num;
                num3 := num;
                num4 := num;
                num5 := num;
            end
            else if i = 20 then
            begin
                num2 := num;
                num3 := num;
                num4 := num;
                num5 := num;
            end
            else if i = 30 then
            begin
                num3 := num;
                num4 := num;
                num5 := num;
            end
            else if i = 40 then
            begin
                num4 := num;
                num5 := num;
            end
            else if i = 200 then
                num5 := num;
        end
        return array(num1, num2, num3, num4, num5);
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

            if MonthsBetween(one_day, prev_one_day) > 1 then
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

function time_diff(time1, time2);
begin
    hour1 := StrToInt(time1[1:2]);
    min1 := StrToInt(time1[4:5]);
    sec1 := StrToInt(time1[7:8]);

    hour2 := StrToInt(time2[1:2]);
    min2 := StrToInt(time2[4:5]);
    sec2 := StrToInt(time2[7:8]);

    ret := hour1 * 3600 + min1 * 60 + sec1 - hour2 * 3600 - min2 * 60 - sec2;
    return ret;
end

function 计算买入(stock_name, stock_code, day, cur_zt);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_3s()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"],
        ['low'],
        ['high'],
        ['amount']
        from tradetable datekey day to day+0.99999 of DefaultStockID() end;
    end

    buy_amount := 0;
    zt_time := "00:00:00";
    first_idx := 0;
    for idx in data do
    begin
        if data[idx]['时间'] < "09:30:00" then
        begin
            first_idx := idx;
            continue;
        end

        if idx = first_idx + 1 then
            continue;

        b1 := false;
        if data[idx]['high'] = cur_zt and data[idx - 1]['close'] <> cur_zt then
            b1 := true;
        b2 := false;
        if idx <> length(data) - 1 and data[idx]['low'] <> cur_zt and data[idx + 1]['high'] = cur_zt then
            b2 := true;
        if b1 or b2 then
        begin
            zt_time := data[idx]['时间'];
            for i := idx - 1 downto 0 do
            begin
                if time_diff(zt_time, data[i]['时间']) <= 60 then
                    buy_amount += data[i]['amount'];
                else
                    break;
            end
            break;
        end
    end
    return array(buy_amount, zt_time);
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
