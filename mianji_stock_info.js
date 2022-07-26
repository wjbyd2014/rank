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
        上市天数 := StockGoMarketDays();

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
        '上涨起点日':上涨起点日, '涨板打断次数':涨板打断次数));
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
    第n天 := StockEndTPrevNDay(上市日, -(几日内 + 创几日新高 - 2));

    回溯天数 := 1; // 回溯多少天
    while True do
    begin
        日期1 := DateToStr(StockEndTPrevNDay(day, 回溯天数)); // 回溯日
        回溯日 := StockEndTPrevNDay(day, 回溯天数);

        if 回溯日 < 第n天 then
            return 上市天数 - 2;

        if 几日内创过几日新高(stock_name, stock_code, day, 回溯天数, 几日内, 创几日新高) then
            回溯天数 += 1; // 回溯日n1日内创过n2日新高，继续向前回溯
        else
            break;
    end
    return 回溯天数 - 1;
end

function 上涨期间涨停板打算次数(stock_name, stock_code, day, num);
begin
    //echo 'begin = ', DateToStr(StockEndTPrevNDay(day, 1));
    //echo 'end = ', DateToStr(StockEndTPrevNDay(day, num));

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
                //echo '涨板打断 ', DateToStr(StockEndTPrevNDay(day, i));
            end

            last_day_is_zt := 0;
        end
    end
    return ret;
end
