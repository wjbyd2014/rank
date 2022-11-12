Function 印象分();
Begin
    day := IntToDate({day});

    昨日大盘涨幅 := count_昨日大盘涨幅(day);
    放量成交额 := 300000000;
    三年前 := IncDay(day, -365 * 3);

    ret := array();
    stock_list := getbk('A股');
    stock_list::begin
        stock_code := mcell;
        stock_name := stockName(stock_code);

        if not (stock_code like 'SZ|SH') then
            continue;

        if stock_name like 'ST|退' then
            continue;

        if not is_trade_day(day, stock_code) then
            continue;

        上市天数 := 计算自定义上市天数(stock_code, day);
        with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
        begin
            昨日收盘价 := ref(close(), 1);
            前日收盘价 := ref(close(), 2);
            昨日涨幅 := count_ratio(昨日收盘价, 前日收盘价);
            if 昨日涨幅 <= 5 then
                continue;

            相对大盘涨幅 := 昨日涨幅 - 昨日大盘涨幅;

            成交金额 := count_amount(15);
            if length(成交金额) <> 16 then
                continue;

            成交金额 := count_amount(10);
            assert(length(成交金额) = 11);
            昨日成交金额 := 成交金额[9];
            if 昨日成交金额 < 放量成交额 then
                continue;

            过去2到10天最大成交金额 := 成交金额[0];
            for i := 1 to 8 do
            begin
                if 成交金额[i] > 过去2到10天最大成交金额 then
                    过去2到10天最大成交金额 := 成交金额[i];
            end

            if 过去2到10天最大成交金额 < 放量成交额 then
                continue;

            创10日新高 := count_创n日新高(10);
            创15日新高 := count_创n日新高(15);

            涨停 := count_涨停(day);

            开盘价 := open();
            开盘涨幅 := count_ratio(开盘价, 昨日收盘价);
            开盘量 := count_开盘量(stock_code, day);

            过去3年涨停板数 := count_过去3年涨停板数(三年前, day);
            if 过去3年涨停板数 < 3 then
                continue;

            ma5上涨起始日 := count_ma_start_day(day, 5);
            ma10上涨起始日 := count_ma_start_day(day, 10);

            str_ma5上涨起始日 := DateToStr(ma5上涨起始日);
            str_ma10上涨起始日 := DateToStr(ma10上涨起始日);

            昨日换手率 := StockHsl4(StockEndTPrevNDay(day, 1));
            过去3年最高换手率 := count_过去3年最高换手率(三年前, day, ma10上涨起始日);
            历史最高换手率日 := 过去3年最高换手率[1];
            历史最高换手率 := 过去3年最高换手率[0];
            if 昨日换手率 < 历史最高换手率 * 0.6 then
                continue;

            阳线实体分 := count_阳线实体(ma5上涨起始日, day, 1);
            印象分 := count_印象分(ma5上涨起始日, day, stock_code);

            ret &= array(('名称':stock_name, '代码':stock_code,
                '昨日涨幅':昨日涨幅, '相对大盘涨幅':相对大盘涨幅,
                '上市天数':上市天数,
                '昨日成交金额':昨日成交金额, '过去2到10天最大成交金额':过去2到10天最大成交金额,
                '7日涨停数':涨停[0], '10日涨停数':涨停[1], '15日涨停数':涨停[2],
                '创10日新高':创10日新高, '创15日新高':创15日新高,
                'ma5上涨起始日':str_ma5上涨起始日, 'ma10上涨起始日':str_ma10上涨起始日,
                '开盘涨幅':开盘涨幅, '开盘价':开盘价, '买入量':开盘量,
                '昨日换手率':昨日换手率, '历史最高换手率':历史最高换手率,'历史最高换手率日':历史最高换手率日,
                '印象':印象分, '阳线实体':阳线实体分));
        end
    end
    return exportjsonstring(ret);
End;

function count_昨日大盘涨幅(day);
begin
    with *,array(pn_Stock():'SH000852', pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        大盘前日收盘价 := ref(close(), 2);
        大盘昨日收盘价 := ref(close(), 1);
        return count_ratio(大盘昨日收盘价, 大盘前日收盘价);
    end
end

function count_amount(day_num);
begin
    return nday3(day_num + 1, amount());
end

function count_创n日新高(day_num);
begin
    arr_close := nday3(day_num + 1, close());
    for i := 0 to day_num - 2 do
    begin
        if arr_close[day_num - 1] <= arr_close[i] then
            return 0;
    end
    return 1;
end

function count_涨停(day);
begin
    n1 := 0;
    n2 := 0;
    n3 := 0;
    n := 0;
    for i := 1 to 15 do
    begin
        one_day := StockEndTPrevNDay(day, i);
        zt := StockIsZt(one_day);
        if zt = 1 then
            n += 1;

        if i = 7 then
            n1 := n;
        if i = 10 then
            n2 := n;
        if i = 15 then
            n3 := n;
    end
    return array(n1, n2, n3);
end

function count_过去3年涨停板数(begin_day, day);
begin
    上市日 := FundGoMarketDate();
    ret := 0;
    i := 1;
    while True do
    begin
        one_day := StockEndTPrevNDay(day, i);
        if DateToInt(one_day) < 上市日 then
            break;

        if one_day < begin_day then
            break;

        if StockIsZt(one_day) = 1 then
            ret += 1;

        i += 1;
    end
    return ret;
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

function count_过去3年最高换手率(begin_day, day, before_day);
begin
    上市日 := FundGoMarketDate();
    i := 1;
    best_hsl := 0;
    str_best_hsl_day := 'N/A';
    while True do
    begin
        one_day := StockEndTPrevNDay(day, i);
        str_one_day := DateToStr(one_day);
        if DateToInt(one_day) < 上市日 then
            break;

        if one_day < begin_day then
            break;

        if one_day >= before_day then
        begin
            i += 1;
            continue;
        end

        hsl := StockHsl4(one_day);
        if hsl > best_hsl then
        begin
            str_best_hsl_day := str_one_day;
            best_hsl := hsl;
        end
        i += 1;
    end
    return array(best_hsl, str_best_hsl_day);
end

function count_阳线实体(before_day, day, min_incr);
begin
    上市日 := FundGoMarketDate();
    i := 1;
    ret := 0;
    while True do
    begin
        one_day := StockEndTPrevNDay(day, i);
        if DateToInt(one_day) < 上市日 then
            break;

        if one_day < before_day then
            break;

        one_day_close := StockClose(one_day);
        one_day_open := StockOpen4(one_day);
        one_day_close_incr := count_ratio(one_day_close, one_day_open);
        if one_day_close_incr > 1 then
            ret += one_day_close_incr;
        i += 1;
    end
    return ret;
end

function count_开盘量(stock_code, day);
begin
    param := BackUpSystemParameters();
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ['vol']
        from tradetable datekey day to day+StrToTime("09:30:00") of DefaultStockID() end;
    end

    RestoreSystemParameters(param);
    ret := 0;
    for idx in data do
    begin
        if data[idx]['时间'] >= '09:30:00' then
            break;
        ret += data[idx]['vol'];
    end
    return ret;
end

function count_黄线(stock_code, one_day);
begin
    param := BackUpSystemParameters();
    with *,array(pn_Stock():stock_code, pn_date():one_day, pn_rate():2, pn_rateday():one_day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ['amount'],
        ['vol']
        from markettable datekey one_day to one_day+0.99999 of DefaultStockID() end;
    end

    sum_amount := 0;
    sum_vol := 0;
    for idx in data do
    begin
        sum_vol += data[idx]['vol'];
        sum_amount += data[idx]['amount'];
    end
    RestoreSystemParameters(param);
    return sum_amount / sum_vol;
end

function count_缩量(i);
begin
    当日成交量 := ref(vol(), i);
    前N日平均成交量 := ref(ma(vol(), 5), i + 1);
    量比 := 当日成交量 / 前N日平均成交量 * 100;
    return 量比 < 50;
end

function count_印象分(before_day, day, stock_code);
begin
    str_before_day := DateToStr(before_day);
    上市日 := FundGoMarketDate();
    i := 1;
    ret := 0;
    while True do
    begin
        one_day := StockEndTPrevNDay(day, i);
        prev_day := StockEndTPrevNDay(day, i + 1);
        str_one_day := datetostr(one_day);
        str_prev_day := datetostr(prev_day);
        if DateToInt(prev_day) < 上市日 then
            break;

        if prev_day < before_day then
            break;

        if StockIsZt2(prev_day) then
        begin
            i += 1;
            continue;
        end

        one_day_close := StockClose(one_day);
        prev_day_price := count_黄线(stock_code, prev_day);
        if one_day_close <= prev_day_price then
            break;
        else
            score := count_ratio(one_day_close, prev_day_price);
            缩量 := count_缩量(i + 1);
            if 缩量 = 1 then
                score *= 0.8;
            ret += score;
        i += 1;
    end
    return ret;
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

Function is_trade_day(day, stock_code);
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
