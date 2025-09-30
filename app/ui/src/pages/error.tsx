import { useLocation } from "react-router";

export const ErrorPage = () => {
  const location = useLocation();
  const truncatedPathname = () => {
    const MAXLEN = 24
    if (location.pathname.length > MAXLEN) {
      return location.pathname.substring(0, MAXLEN - 3) + "..."
    }
    return location.pathname
  };

  return (
    <>
      <div className="mx-auto my-8 flex max-w-sm items-center gap-x-10 rounded-xl bg-white p-6 shadow-lg outline outline-black/5 dark:bg-neutral-800 dark:shadow-none dark:-outline-offset-1 dark:outline-white/10">
        <img className="size-12 shrink-0 mx-auto" src="/public/icon.svg" />
        <div className="mx-auto">
          <div className="text-xl font-medium text-black dark:text-white"><b>404</b></div>
          <p className="text-gray-500 dark:text-gray-400">The endpoint <code className="dark:bg-gray-800">{truncatedPathname()}</code> doesn't exist.</p>
        </div>
      </div>
    </>
  )
};