## Code to execute one test context.
module Context${context_id} where

import qualified ${submission_name}
import System.IO (hPutStr, stderr)
import qualified Evaluator${context_id}

main = do
    ## In Haskell we do the before/after inside the main (?)
    ${before}
    ## Call main function
    % if execution.exists:
        ${submission_name}.main
    % endif
    % for additional in additionals:
        hPutStr stderr "--${secret_id}-- SEP"
        putStr "--${secret_id}-- SEP"
        appendFile "${output_file}" "--${secret_id}-- SEP"
        % if additional.has_return:
            v${loop.index} <- ${submission_name}.<%include file="function.mako" args="function=additional.function" />
            Evaluator${context_id}.evaluate_${context_id}_${loop.index} v${loop.index}
        % else:
            ${submission_name}.<%include file="function.mako" args="function=additional.function" />
        % endif
    % endfor
    ${after}
