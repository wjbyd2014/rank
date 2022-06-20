Function 分钟线趋势();
Begin
    day := IntToDate({day});

    最高价最少涨幅阈值 := 5;
    最后收盘价最少涨幅阈值 := 2.5;
    最后均价最少涨幅阈值 := 2.5;
    白线维持拉高次数 := 20;
    白线拉高阈值 := 3;
    黄白线响度高度开始计算时间 := "10:00:00";
    白线维持高于黄线次数 := 20;
    白线无视黄线阈值 := 3;

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

        data := count_1m(
            day, stock_code, stock_name,
            最高价最少涨幅阈值,
            最后收盘价最少涨幅阈值,
            最后均价最少涨幅阈值,
            白线维持拉高次数,
            白线拉高阈值,
            黄白线响度高度开始计算时间,
            白线维持高于黄线次数,
            白线无视黄线阈值
        );
        if data <> Nil then
            ret &= data;
    end
    return exportjsonstring(ret);
End;

Function count_1m(day, stock_code, stock_name,
    最高价最少涨幅阈值,
    最后收盘价最少涨幅阈值,
    最后均价最少涨幅阈值,
    白线维持拉高次数,
    白线拉高阈值,
    黄白线响度高度开始计算时间,
    白线维持高于黄线次数,
    白线无视黄线阈值);
begin
    day_str := DateToStr(day);
    with *,array(pn_Stock():stock_code, PN_Date():day, pn_rate():2, pn_rateday():day) do
    begin
        昨日收盘价 := ref(close(), 1);

        if 昨日收盘价 = 0 then
            return Nil;

        今日开盘价 := open();
    end

    with *,array(pn_Stock():stock_code, pn_rate():2, pn_rateday():day) do
    begin
        今日涨停价 := StockZtClose(day);

        // 一字涨停不要
        if StockIsZt2(day) then
            return Nil;
    end

    with *,array(pn_Stock():stock_code, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
            ["StockID"] as "代码",
            ["StockName"] as "名称",
            TimeToStr(["date"]) as "时间",
            ["open"] as "开盘价",
            ["high"] as "最高价",
            ["price"] as "收盘价",
            ['sectional_amount']/['sectional_vol'] as "均价"
        from markettable datekey day to day+0.99999 of DefaultStockID() where timetostr(timeof(['date'])) <= "10:30:00"  end;
    end

    最高价 := 0;
    白线拉高次数 := 0;
    黄线高于白线次数 := 0;
    for i := 0 to length(data) - 1 do
    begin
        最高价_ := data[i]['最高价'];
        if 最高价_ > 最高价 then
            最高价 := 最高价_;

        收盘价 := data[i]['收盘价'];
        收盘价涨幅 := (收盘价 / 昨日收盘价 - 1) * 100;

        if 收盘价涨幅 > 白线拉高阈值 then
            白线拉高次数 += 1;

        if data[i]['时间'] >= 黄白线响度高度开始计算时间 then
            if 收盘价涨幅 > 白线无视黄线阈值 or 收盘价 > data[i]["均价"] then
                白高于黄线次数 += 1;

        if i = length(data) - 1 then
        begin
          最后收盘价 := data[i]["收盘价"];
          最后均价 := data[i]["均价"];
        end
    end

    最高价涨幅 := (最高价 / 昨日收盘价 - 1) * 100;
    if 最高价涨幅 < 最高价最少涨幅阈值 then
        return Nil;

    if 白线拉高次数 < 白线维持拉高次数 then
        return Nil;

    if 白高于黄线次数 < 白线维持高于黄线次数 then
        return Nil;

    if 今日开盘价 > 最后收盘价 then
        return Nil;

    最后收盘价涨幅 := (最后收盘价 / 昨日收盘价 - 1) * 100;
    if 最后收盘价涨幅 < 最后收盘价最少涨幅阈值 then
        return Nil;

    最后均价涨幅 := (最后均价 / 昨日收盘价 - 1) * 100;
    if 最后均价涨幅 < 最后均价最少涨幅阈值 then
        return Nil;

    if 最后收盘价 = 今日涨停价 then
        return Nil;

    return array((
        '代码' : stock_code,
        '名称' : stock_name,
        '最高价涨幅' : formatfloat('0.00', 最高价涨幅),
        '最后均价涨幅' : formatfloat('0.00', 最后均价涨幅),
        '最后收盘价涨幅' : formatfloat('0.00', 最后收盘价涨幅),
        '白线过3%分钟数' : 白线拉高次数,
        '白线高于黄线分钟数' : 白高于黄线次数
        ));
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
