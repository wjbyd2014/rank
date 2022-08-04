Function 面积2股票信息();
Begin
    day := {day};
    stock_code := '{stock_code}';
    stock_name := StockName(stock_code);

    ret := count_stock_info(stock_name, stock_code, day);
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
    end
    return array(('上市天数':上市天数, 'ma3向上':ma3向上, 'ma5向上':ma5向上,
        '上涨起点日':上涨起点日, '涨板打断次数':涨板打断次数, '开盘价涨幅':开盘价涨幅, '昨日是否一字板':昨日是否一字板));
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

        if stockiszt(回溯日) then
        begin
            回溯天数 += 1; // 当日涨停，继续向前回溯
            continue
        end

        if 回溯日 = 上市日 then
        begin
            return 回溯天数;
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
