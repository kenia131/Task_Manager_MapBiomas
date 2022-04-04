#to access database
psql -U mapbiomer -W -h 200.201.194.155 mapbiomas

#list tasks with duration
select  code, state, extract(EPOCH from (end_date - start_date)/60 ) as duration, start_date, end_date from tasks;
update tasks set state='UNSUBMITTED' where code like '%annual_caatinga_100t_30000b%' and state != 'COMPLETED';
update tasks set state='UNSUBMITTED' where code like '%annual_caatinga_100t_30000b%' and state != 'CANCEL_REQUESTED';

#
delete from logs as l where l.task in (select id from tasks as t where t.code like '%classification/annual/L5_T1_TOA%');
delete from tasks as t where t.code like '%classification/annual/L5_T1_TOA%';
