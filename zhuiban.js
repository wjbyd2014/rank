Function 追板();
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

        买入 := 计算买入(stock_name, stock_code, day);
        if 买入[0] = 0 then
            continue;

        涨停 := 计算涨停板(stock_code, day);
        最高价 := 计算最高价(stock_name, stock_code, day);
        涨幅 := 计算涨幅(stock_name, stock_code, day);
        买入量 := int(500 * 10000 / 买入[0]);
        ret &= array(('名称':stock_name, '代码':stock_code,
                '买入价':买入[0], '买入时间':买入[1], '买入量':买入量,
                '3日最高价':最高价[0], '5日最高价':最高价[1], '7日最高价':最高价[2],
                '10日最高价':最高价[3], '15日最高价':最高价[4], '30日最高价':最高价[5],
                '3日涨幅':涨幅[0], '5日涨幅':涨幅[1], '7日涨幅':涨幅[2],
                '1日涨停数':涨停[0], '2日涨停数':涨停[1], '3日涨停数':涨停[2],
                '5日涨停数':涨停[3], '7日涨停数':涨停[4], '10日涨停数':涨停[5],
                '15日涨停数':涨停[6], '30日涨停数':涨停[7]));
    end;
    return exportjsonstring(ret);
End;

function 计算涨幅(stock_name, stock_code, day);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        close1_ := ref(close(), 1);
        close4_ := ref(close(), 4);
        close6_ := ref(close(), 6);
        close8_ := ref(close(), 8);

        zf3 := count_ratio(close1_, close4_);
        zf5 := count_ratio(close1_, close6_);
        zf7 := count_ratio(close1_, close8_);
    end
    return array(zf3, zf5, zf7);
end

function 计算最高价(stock_name, stock_code, day);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        data := ref(nday(30, '时间', datetimetostr(sp_time()), '当日高价',high()), 1);
        if data = 0 then
            return array(0, 0, 0, 0, 0, 0);

        data_high := data[:, '当日高价'];
    end

    highest := 0;
    num3 := 0;
    num5 := 0;
    num7 := 0;
    num10 := 0;
    num15 := 0;
    num30 := 0;
    len := length(data);
    for i := len downto 0 do
    begin
        if data_high[i] > highest then
            highest := data_high[i];

        if i = len - 3 then
            num3 := highest;
        else if i = len - 5 then
            num5 := highest;
        else if i = len - 7 then
            num7 := highest;
        else if i = len - 10 then
            num10 := highest;
        else if i = len - 15 then
            num15 := highest;
        else if i = len - 30 then
            num30 := highest;
    end
    return array(num3, num5, num7, num10, num15, num30);
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
        ["close"]
        from markettable datekey day to day+0.99999 of DefaultStockID() end;
    end

    第一个非涨停价 := 0;
    for idx in data do
    begin
        if data[idx]['close'] <> 当日涨停价 then
        begin
            第一个非涨停价 := data[idx]['close'];
            continue;
        end
        else
        begin
            if 第一个非涨停价 <> 0 then
            begin
                buy_price := data[idx]['close'];
                buy_time := data[idx]['时间'];
                break;
            end
        end
    end
    return array(buy_price, buy_time);
end


function 计算涨停板(stock_code, day);
begin
    num1 := 0;
    num2 := 0;
    num3 := 0;
    num5 := 0;
    num7 := 0;
    num10 := 0;
    num15 := 0;
    num30 := 0;

    num := 0;
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        ret := 0;
        for i := 1 to 30 do
        begin
            one_day := StockEndTPrevNDay(day, i);
            if StockIsZt(one_day) then
                num += 1;

            if i = 1 then
                num1 := num;
            else if i = 2 then
                num2 := num;
            else if i = 3 then
                num3 := num;
            else if i = 5 then
                num5 := num;
            else if i = 7 then
                num7 := num;
            else if i = 10 then
                num10 := num;
            else if i = 15 then
                num15 := num;
            else if i = 30 then
                num30 := num;
        end
        return array(num1, num2, num3, num5, num7, num10, num15, num30);
    end
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
