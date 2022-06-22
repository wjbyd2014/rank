Function 分钟线策略买入计算();
Begin
    day := {day};
    stock_code := '{stock_code}';
    vol_ratio := 0.2;

    with *,array(pn_Stock():stock_code, pn_rate():2, pn_rateday():day) do
    begin
        今日涨停价 := StockZtClose(day);
    end

    with *,array(pn_Stock():stock_code, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
            TimeToStr(["date"]) as "时间",
            ["vol"] as "成交量",
            ["price"] as "收盘价",
            ['sectional_amount']/['sectional_vol'] as "均价"
        from markettable datekey day to day+0.99999 of DefaultStockID() where timetostr(timeof(['date'])) <= "10:30:00"  end;
    end

    sum_price := 0;
    num_price := 0;
    arr_vol := array();
    for i := 0 to length(data) - 1 do
    begin
        if data[i]["时间"] > "10:25:00" then
        begin
            if data[i]["收盘价"] <> 今日涨停价 then
            begin
                sum_price += data[i]["收盘价"];
                num_price += 1;
            end
        end
        else
        begin
            arr_vol &= array(data[i]["成交量"]);
        end
    end

    buy_price := 0;
    buy_vol := 0;

    if num_price > 0 then
    begin
        buy_price := FloatN(sum_price / num_price, 3);

        sortarray(arr_vol);

        sum_vol := 0;
        for j := 10 to 19 do
        begin
            sum_vol += arr_vol[j];
        end

        buy_vol := int(sum_vol / 10 * num_price * vol_ratio);
    end
    return array(buy_price, buy_vol);
End;
