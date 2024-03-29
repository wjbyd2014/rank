Function 面积2每日股票池信息();
Begin
    day := IntToDate({day});

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

        stock_info := count_stock_info(stock_name, stock_code, day);
        ret &= stock_info
    end
    return exportjsonstring(ret);
End;

function count_stock_info(stock_name, stock_code, day);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        昨日收盘价 := ref(close(), 1);
        今日涨停价 := StockZtClose(day);
        上市天数 := 计算自定义上市天数(stock_code, day);

        今日开盘价 := open();
        开盘价涨幅 := count_ratio(今日开盘价, 昨日收盘价);
        if 昨日收盘价 = 0 then
            开盘价涨幅 := 0;

        开盘价涨停 := 0;
        if 今日开盘价 = 今日涨停价 then
            开盘价涨停 := 1;

        昨日是否一字板 := stockiszt2(StockEndTPrevNDay(day, 1));

        昨日3日均线 := ref(ma(close(), 3), 1);
        前日3日均线 := ref(ma(close(), 3), 2);
        if 昨日3日均线 > 前日3日均线 then
            ma3向上 := 1;
        else
            ma3向上 := 0;

        昨日5日均线 := ref(ma(close(), 5), 1);
        前日5日均线 := ref(ma(close(), 5), 2);
        if 昨日5日均线 > 前日5日均线 then
            ma5向上 := 1;
        else
            ma5向上 := 0;

        上涨起点 := 寻找上涨起点(stock_name, stock_code, day, 上市天数, 3, 3);
        if 上涨起点 = 0 then
        begin
            上涨起点日 := '';
            涨板打断次数 := 0;
        end
        else
        begin
            上涨起点日 := DateToStr(StockEndTPrevNDay(day, 上涨起点));
            涨板打断次数 := 上涨期间涨停板打算次数(stock_name, stock_code, day, 上涨起点);
        end

        低位涨停板 := 计算低位涨停板(stock_name, stock_code, day);
        assert(length(低位涨停板) = 5);

        十日阴线数 := 计算十日阴线数(stock_name, stock_code);

        十字阴线极值 := 计算十字阴线极值(stock_name, stock_code);

        连扳数 := 计算连扳(stock_name, stock_code, day);

        十日最大两个天量之和 := 计算天量(stock_name, stock_code, day);

        昨天缩量大涨 := 计算缩量大涨(stock_name, stock_code, day, 1);
        前天缩量大涨 := 计算缩量大涨(stock_name, stock_code, day, 2);
    end

    return array(('名称':stock_name, '代码':stock_code, '上市天数':上市天数, 'ma3向上':ma3向上, 'ma5向上':ma5向上,
        '开盘价涨停': 开盘价涨停,
        '上涨起点日':上涨起点日, '涨板打断次数':涨板打断次数, '开盘价涨幅':开盘价涨幅, '昨日是否一字板':昨日是否一字板,
        '1日低位涨停板数':低位涨停板[0], '3日低位涨停板数':低位涨停板[1], '5日低位涨停板数':低位涨停板[2],
        '7日低位涨停板数':低位涨停板[3], '10日低位涨停板数':低位涨停板[4],
        '10日阴线数':十日阴线数,
        '3日十字阴线极值':十字阴线极值[0],
        '5日十字阴线极值':十字阴线极值[1],
        '10日十字阴线极值':十字阴线极值[2],
        '连扳数':连扳数,
        '10日最大两个天量之和':十日最大两个天量之和,
        '昨天缩量大涨': 昨天缩量大涨, '前天缩量大涨':前天缩量大涨
        ));
end

function 计算缩量大涨(stock_name, stock_code, day, num);
begin
    data := ref(nday(11, '时间', datetimetostr(sp_time()), '成交量', vol()), num);
    if data = 0 or length(data) <> 11 then
        return 0;

    day_vol := data[10]['成交量'];
    data_vol := data[0:9, '成交量'];
    sortarray(data_vol, False);
    avg_vol := (data_vol[0] + data_vol[1]) / 4;
    if day_vol > avg_vol then
        return 0;

    day_close := ref(close(), num);
    prev_day_close := ref(close(), num + 1);
    if count_ratio(day_close, prev_day_close) < 10 then
        return 0;
    return 1;
end

function 计算天量(stock_name, stock_code, day);
begin
    data := ref(nday(10, '时间', datetimetostr(sp_time()), '成交额',amount()), 1);

    if data = 0 or length(data) < 2 then
        return 0;

    data_amount := data[:, '成交额'];
    sortarray(data_amount, False);
    top2 := data_amount[0] + data_amount[1];
    return int(top2 / 100000000);
end

function 计算连扳(stock_name, stock_code, day);
begin
    ret := 0;
    i := 1;
    while True do
    begin
        if StockIsZt(StockEndTPrevNDay(day, i)) then
        begin
            ret += 1;
            i += 1;
        end
        else
            break;
    end
    return ret;
end

function 计算十字阴线极值(stock_name, stock_code);
begin
    num5 := 0;
    num3 := 0;
    num := 0;
    for i := 1 to 10 do
    begin
        if i = 4 then
            num3 := num;
        if i = 6 then
            num5 := num;

        昨日收盘价 := ref(close(), i + 1);
        当日开盘价 := ref(open(), i);
        当日收盘价 := ref(close(), i);
        当日最高价 := ref(high(), i);
        当日最低价 := ref(low(), i);

        if 当日开盘价 <= 当日收盘价 then
            continue;

        日内跌幅 := count_ratio(当日开盘价, 当日收盘价);
        最高价涨幅 := count_ratio(当日最高价, 昨日收盘价);
        最低价涨幅 := count_ratio(当日最低价, 昨日收盘价);
        日内振幅 := 最高价涨幅 - 最低价涨幅;
        差值 := 日内振幅 - 日内跌幅;
        if 差值 > num then
            num := 差值;
    end
    return array(num3, num5, num);
end

function 计算十日阴线数(stock_name, stock_code);
begin
    ret := 0;
    for i := 1 to 10 do
    begin
        day_open := ref(open(), i);
        day_close := ref(close(), i);
        if day_open > day_close then
            ret += 1;
    end
    return ret;
end

function 计算低位涨停板(stock_name, stock_code, day);
begin
    ret := Zeros(5);
    for i := 1 to 10 do
    begin
        当日 := DateToStr(StockEndTPrevNDay(day, i));
        if StockIsZt(StockEndTPrevNDay(day, i)) then
        begin
            当日收盘价 := ref(close(), i);
            前四日最低价 := ref(close(), i + 1);
            for j := 2 to 4 do
            begin
                前N日收盘价 := ref(close(), i + j);
                if 前N日收盘价 < 前四日最低价 then
                    前四日最低价 := 前N日收盘价;
            end

            ratio := 15;
            if stock_code[3:4] = '30' or stock_code[3:4] = '68' then
                ratio := 30;

            涨幅 := count_ratio(当日收盘价, 前四日最低价);
            if 涨幅 > ratio then
                continue;

            if i = 1 then
                ret[0] += 1
            else if i <= 3 then
                ret[1] += 1
            else if i <= 5 then
                ret[2] += 1
            else if i <= 7 then
                ret[3] += 1
            else
                ret[4] += 1
        end
    end
    return ret;
end

function 计算自定义上市天数(stock_code, day);
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
    return day - 下一日;
end

function 创n日新高(stock_name, stock_code, day, 回溯天数, 创几日新高);
begin
    close1 := ref(close(), 回溯天数);
    for i := 1 to 创几日新高 - 1 do
    begin
        日期3 := DateToStr(StockEndTPrevNDay(day, i + 回溯天数));

        close2 := ref(close(), i + 回溯天数);
        if close1 < close2  then
            return False; // 没创n日新高
    end
    return True;
end

function 几日内创过几日新高(stock_name, stock_code, day, 回溯天数, 几日内, 创几日新高);
begin
    for i := 0 to 几日内 - 1 do
    begin
        日期2 := DateToStr(StockEndTPrevNDay(day, i + 回溯天数)); // 判断日
        if 创n日新高(stock_name, stock_code, day, i + 回溯天数, 创几日新高) then
            return True;
    end
    return False;
end

function 寻找上涨起点(stock_name, stock_code, day, 上市天数, 几日内, 创几日新高);
begin
    上市日 := StockFirstDay(stock_code);

    if day = 上市日 then
        return 0;

    回溯天数 := 1; // 回溯多少天
    while True do
    begin
        日期1 := DateToStr(StockEndTPrevNDay(day, 回溯天数)); // 回溯日
        回溯日 := StockEndTPrevNDay(day, 回溯天数);

        if 回溯日 = 上市日 then
        begin
            return 回溯天数;
        end
        
        if stockiszt(回溯日) then
        begin
            回溯天数 += 1; // 当日涨停，继续向前回溯
            continue
        end

        if 几日内创过几日新高(stock_name, stock_code, day, 回溯天数, 几日内, 创几日新高) then
            回溯天数 += 1; // 回溯日n1日内创过n2日新高，继续向前回溯
        else
            break;
    end
    return 回溯天数 - 1;
end

function 上涨期间涨停板打算次数(stock_name, stock_code, day, num);
begin
    ret := 0;
    last_day_is_zt := 0;
    for i := num downto 1 do
    begin
        if StockIsZt(StockEndTPrevNDay(day, i)) then
        begin
            last_day_is_zt := 1;
        end
        else
        begin
            if last_day_is_zt = 1 then
            begin
                ret += 1;
            end

            last_day_is_zt := 0;
        end
    end
    return ret;
end

function count_ratio(value1, value2);
begin
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
