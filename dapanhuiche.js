Function 大盘回撤();
Begin
    day := IntToDate({day});

    one_minutes := StrToTime('00:01:00');
    min_minutes := 10;
    max_minutes := 20;
    time1 := StrToTime("9:35:00");
    time2 := StrToTime("10:30:00");
    time3 := StrToTime("11:00:00");
    last_最大跌幅持续时间 := 0;

    while True do
    begin
         with *,array(pn_Stock():'SH000852', pn_date():day, pn_rate():0, pn_rateday():0, PN_Cycle():cy_1m()) do
         begin
              data := select
                  TimeToStr(["date"]) as "时间",
                  floatn(["close"], 3) as "close"
                  from markettable datekey day+time1 to day+time2 of DefaultStockID() end;
         end

         data_close := data[:,'close'];
         最大跌幅 := MaxDrawDown(data_close, 0, max_minutes);
         最大跌幅持续时间 := 最大跌幅[1] - 最大跌幅[0];

         if 最大跌幅持续时间 > last_最大跌幅持续时间 then
         begin
             last_最大跌幅持续时间 := 最大跌幅持续时间;
             最大跌幅开始时间 := data[最大跌幅[0]]['时间'];
             最大跌幅结束时间 := data[最大跌幅[1]]['时间'];
             最大跌幅百分比 := floatn(最大跌幅[3] * 100, 2);
         end

        if 最大跌幅持续时间 < min_minutes then
        begin
            if TimeToStr(time2) < TimeToStr(time3) then
            begin
                time1 += one_minutes;
                time2 += one_minutes;
                continue;
            end
        end
        // 要么找到超过10分钟的回撤区间了，要么已经算到11点了
        break;
    end
    return exportjsonstring(array(('最大回撤开始时间':最大跌幅开始时间, '最大回撤结束时间':最大跌幅结束时间, '最大跌幅持续时间':last_最大跌幅持续时间, '最大跌幅百分比':最大跌幅百分比)));
End;
