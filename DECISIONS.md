

I used 3 fasterwhisper models like small,medium and finally large-v3-turbo.Small and medium provided transcriptions that is somewhat garbage or does not
match the audio content from testdata.Finally large-v3-turbo results somewhat matched the audio content if not entirely.If my current pc had power gpu
support I would have used a bigger and stronger model for better accuracy.


I recorded a youtube video that has both english and bengali audio using a phone recoder.This is kept in testdata directory and used as real testdata for
Real Adapter transcriber

I wrote 4 json files in recordings directory as fake audio content for using testdata for Mock transcriber.